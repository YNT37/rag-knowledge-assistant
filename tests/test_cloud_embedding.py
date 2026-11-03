import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import OpenAIError

from app.core import kb_state
from app.services import embedding_service, rag_service


@pytest.fixture(autouse=True)
def reset_index(monkeypatch):
    monkeypatch.setattr(rag_service, "model", None)
    monkeypatch.setattr(rag_service, "chunks", [])
    monkeypatch.setattr(rag_service, "chunk_embeddings", None)
    monkeypatch.setattr(rag_service, "index_identity", None)
    monkeypatch.setattr(kb_state, "index_dirty", True)


@pytest.fixture
def cloud_env(monkeypatch):
    for key, value in {
        "EMBEDDING_BACKEND": "siliconflow",
        "EMBEDDING_API_KEY": "test-key-only",
        "EMBEDDING_BASE_URL": "https://example.invalid/v1",
        "EMBEDDING_MODEL": "test-embedding-model",
    }.items():
        monkeypatch.setenv(key, value)


def test_cloud_retrieval_uses_same_model_and_reuses_index(cloud_env, monkeypatch):
    docs = [
        {"source": "a.md", "chunk_id": 0, "content": "alpha"},
        {"source": "b.md", "chunk_id": 0, "content": "beta"},
    ]
    vectors = {"alpha": [1.0, 0.0], "beta": [0.0, 1.0], "question": [1.0, 0.0]}
    create = Mock(side_effect=lambda **kw: SimpleNamespace(data=[SimpleNamespace(embedding=vectors[kw["input"]])]))
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    factory = Mock(return_value=client)
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: docs)
    monkeypatch.setattr(embedding_service, "create_embedding_client", factory)

    result = rag_service.search_chunks("question", top_k=2, min_score=0.5)
    assert [(item["source"], item["score"]) for item in result] == [("a.md", 1.0)]
    assert [call.kwargs["input"] for call in create.call_args_list] == ["alpha", "beta", "question"]
    assert all(call.kwargs["model"] == "test-embedding-model" for call in create.call_args_list)
    assert kb_state.index_dirty is False
    rag_service.search_chunks("question", top_k=1, min_score=0.5)
    assert create.call_count == 4
    factory.assert_called_once()


def test_cloud_failure_keeps_index_dirty_and_does_not_commit_partial_vectors(cloud_env, monkeypatch):
    docs = [{"source": "a.md", "chunk_id": 0, "content": "alpha"}, {"source": "b.md", "chunk_id": 0, "content": "beta"}]
    create = Mock(side_effect=[SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])]), OpenAIError("fake secret and error")])
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: docs)
    monkeypatch.setattr(embedding_service, "create_embedding_client", lambda *_: client)
    with pytest.raises(RuntimeError, match="云端向量服务暂不可用") as error:
        rag_service.initialize_rag()
    assert "fake secret" not in str(error.value)
    assert kb_state.index_dirty is True
    assert rag_service.chunks == []
    assert rag_service.chunk_embeddings is None


def test_cloud_config_change_rebuilds_index(cloud_env, monkeypatch):
    docs = [{"source": "a.md", "chunk_id": 0, "content": "alpha"}]
    create = Mock(return_value=SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])]))
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: docs)
    monkeypatch.setattr(embedding_service, "create_embedding_client", lambda *_: client)
    rag_service.initialize_rag()
    monkeypatch.setenv("EMBEDDING_MODEL", "different-model")
    rag_service.initialize_rag()
    assert [call.kwargs["model"] for call in create.call_args_list] == ["test-embedding-model", "different-model"]


def test_empty_cloud_index_does_not_require_key_or_call_service(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BACKEND", "siliconflow")
    for key in ("EMBEDDING_API_KEY", "EMBEDDING_BASE_URL", "EMBEDDING_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: [])
    assert rag_service.search_chunks("question") == []


@pytest.mark.parametrize("vector", [[], [0.0, 0.0], [float("nan"), 1.0]])
def test_bad_cloud_vectors_leave_index_dirty(cloud_env, monkeypatch, vector):
    docs = [{"source": "a.md", "chunk_id": 0, "content": "alpha"}]
    create = Mock(return_value=SimpleNamespace(data=[SimpleNamespace(embedding=vector)]))
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: docs)
    monkeypatch.setattr(embedding_service, "create_embedding_client", lambda *_: client)
    with pytest.raises(RuntimeError):
        rag_service.initialize_rag()
    assert kb_state.index_dirty is True


def test_local_mode_uses_local_model_and_query_prompt(monkeypatch):
    monkeypatch.delenv("EMBEDDING_BACKEND", raising=False)
    docs = [{"source": "a.md", "chunk_id": 0, "content": "alpha"}]
    local_model = Mock()
    local_model.device = "cpu"
    local_model.encode.side_effect = ["doc-vectors", "query-vector"]
    scalar = lambda value: SimpleNamespace(item=lambda: value)
    scores = SimpleNamespace(topk=lambda k: ([scalar(0.9)], [scalar(0)]))
    local_model.similarity.return_value = [scores]
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False), float32="float32"))
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=lambda *args, **kwargs: local_model))
    monkeypatch.setattr(rag_service, "get_model_path", lambda: "fake-model-path")
    monkeypatch.setattr(rag_service, "_load_registered_chunks", lambda: docs)
    assert rag_service.search_chunks("question")[0]["source"] == "a.md"
    assert local_model.encode.call_args_list[0].kwargs == {"batch_size": 32, "show_progress_bar": False}
    assert local_model.encode.call_args_list[1].kwargs == {"prompt_name": "query"}


def test_cloud_malformed_response_does_not_return_fake_vector():
    client = SimpleNamespace(embeddings=SimpleNamespace(create=Mock(return_value=SimpleNamespace(data=[]))))
    with pytest.raises(RuntimeError, match="云端向量服务返回无效结果"):
        embedding_service.embed_cloud_text(client, "text", "model")


def test_cosine_rounding_stays_within_valid_range():
    vector = [0.1, 0.1, 0.3]
    assert rag_service._cosine_similarity(vector, vector) == 1.0
    assert rag_service._cosine_similarity(vector, [-value for value in vector]) == -1.0
