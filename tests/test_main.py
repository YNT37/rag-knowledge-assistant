import pytest

from fastapi.testclient import TestClient
from  fastapi.exceptions import ResponseValidationError
from httpx2 import Request
from openai import APIConnectionError

from app.core import database
from app.services import llm_service
from app.services import rag_service
from main import app

client = TestClient(app)
client_1 = TestClient(app, raise_server_exceptions=False)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_get_missing_task():
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_get_tasks_returns_list():
    response = client.get("/tasks")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)


def test_search_rejects_invalid_limit():
    response = client.get(
        "/search",
        params={"limit": 0},
    )

    assert response.status_code == 422


def test_create_task_rejects_empty_title():
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "done": False,
        }
    )

    assert response.status_code == 422


def test_ai_ask_rejects_empty_question():
    response = client.post(
        "/ai/ask",
        json={
            "question": "",
        }
    )

    assert response.status_code == 422


def test_ai_ask_returns_model_answer(monkeypatch):
    def fake_ask_llm(question: str):
        assert question == "什么是请求体？"
        return "模拟回答"

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "模拟回答"}


def test_ai_ask_returns_503_when_ask_fails(monkeypatch):
    def fake_ask_llm(question: str):
        raise APIConnectionError(
            request=Request("post", "https://example.invalid")
        )

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "模型服务暂不可用"}


def test_ai_ask_returns_502_when_response_is_none(monkeypatch):
    def fake_ask_llm(question: str):
        return None

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}


def test_ai_ask_returns_502_when_response_is_empty(monkeypatch):
    def fake_ask_llm(question: str):
        return ""

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}


def test_ai_ask_returns_502_when_response_is_whitespace(monkeypatch):
    def fake_ask_llm(question: str):
        return "   "

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}


def test_ai_ask_returns_503_when_api_key_is_missing(monkeypatch):
    def fake_ask_llm(question: str):
        return "模拟回答"

    monkeypatch.setattr(llm_service, "api_key", None)
    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "模型服务未配置"}


def test_database_uses_temporary_file(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks_test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)

    database.init_db()

    assert test_db.exists()
    assert database.get_all_tasks() == []


def test_ai_chat_sends_history_and_current_question(monkeypatch):
    monkeypatch.setattr(llm_service, "api_key", "test_key")
    monkeypatch.setattr(llm_service, "base_url", "https://example.invalid")
    monkeypatch.setattr(llm_service, "model", "test_model")

    def fake_ask_llm(messages):
        assert messages == [
            {"role": "system", "content": "你是一名耐心的 Python 老师。"},
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "FastAPI 是后端框架"},
            {"role": "user", "content": "它能做什么？"},
        ]

        return "它可以编写后端 API"

    monkeypatch.setattr(llm_service, "ask_chat", fake_ask_llm)

    response = client.post(
        "/ai/chat",
        json={
            "question": "它能做什么？",
            "history": [
                {"role": "user", "content": "我正在学习 FastAPI"},
                {"role": "assistant", "content": "FastAPI 是后端框架"},
            ],
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "它可以编写后端 API",
        "history": [
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "FastAPI 是后端框架"},
            {"role": "user", "content": "它能做什么？"},
            {"role": "assistant", "content": "它可以编写后端 API"},
        ]
    }


def test_ai_chat_works_without_history(monkeypatch):
    monkeypatch.setattr(llm_service, "api_key", "test_key")
    monkeypatch.setattr(llm_service, "base_url", "https://example.invalid")
    monkeypatch.setattr(llm_service, "model", "test_model")

    def fake_ask_llm(messages):
        assert messages == [
            {"role": "system", "content": "你是一名耐心的 Python 老师。"},
            {"role": "user", "content": "我正在学习 FastAPI"},
        ]

        return "欢迎学习 FastAPI"

    monkeypatch.setattr(llm_service, "ask_chat", fake_ask_llm)

    response = client.post(
        "/ai/chat",
        json={"question": "我正在学习 FastAPI"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "欢迎学习 FastAPI",
        "history": [
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "欢迎学习 FastAPI"},
        ]
    }


def test_ai_rag_returns_answer(monkeypatch):
    def fake_answer_with_rag(question: str):
        assert question == "FastAPI 有什么作用？"
        return {'answer': 'FastAPI 是一个 Python Web 框架', 'sources': [{'source': 'fastapi.md', 'chunk_id': 1, 'content': 'FastAPI 是一个 Python Web 框架'}]}

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "FastAPI 有什么作用？",
        }
    )

    assert response.status_code == 200
    assert response.json() == {'answer': 'FastAPI 是一个 Python Web 框架', 'sources': [{'source': 'fastapi.md', 'chunk_id': 1, 'content': 'FastAPI 是一个 Python Web 框架'}]}


def test_ai_rag_returns_502_when_answer_is_none(monkeypatch):
    def fake_answer_with_rag(question: str):
        return None

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "FastAPI 有什么作用？",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "模型未返回有效回答",
    }


def test_ai_rag_returns_503_when_connection_fails(monkeypatch):
    def fake_answer_with_rag(question: str):
        raise APIConnectionError(
            request=Request(
                "POST",
                "https://example.invalid",
            )
        )

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "FastAPI 有什么作用？",
        }
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "模型服务暂不可用",
    }


def test_ai_rag_returns_503_when_retrieval_initialization_fails(monkeypatch):
    def fake_answer_with_rag(question: str):
        raise RuntimeError("模拟初始化失败")

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client_1.post(
        "/ai/rag",
        json={
            "question": "FastAPI 有什么作用？",
        }
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "检索服务暂不可用",
    }


def test_ai_rag_rejects_whitespace_question(monkeypatch):
    def fake_answer_with_rag(question: str):
        raise AssertionError(
            "无效问题不应该调用 RAG 服务"
        )

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "   ",
        }
    )

    assert response.status_code == 422


def test_ai_rag_rejects_question_longer_than_500_characters(monkeypatch):
    def fake_answer_with_rag(question: str):
        raise AssertionError(
            "无效问题不应该调用 RAG 服务"
        )

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    long_question = "问" * 501

    response = client.post(
        "/ai/rag",
        json={
            "question": long_question,
        }
    )

    assert response.status_code == 422


def test_ai_rag_accepts_question_with_500_characters(monkeypatch):
    def fake_answer_with_rag(question: str):
        assert len(question) == 500
        return {'answer': '模拟回答', 'sources': []}

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    question = "问" * 500

    response = client.post(
        "/ai/rag",
        json={
            "question": question,
        }
    )

    assert response.status_code == 200
    assert response.json() == {'answer': '模拟回答', 'sources': []}


def test_ai_rag_strips_surrounding_whitespace(monkeypatch):
    def fake_answer_with_rag(question: str):
        assert question == "FastAPI 有什么作用？"
        return {'answer': '模拟回答', 'sources': []}

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "   FastAPI 有什么作用？   \n",
        }
    )

    assert response.status_code == 200
    assert response.json() == {'answer': '模拟回答', 'sources': []}


def test_ai_rag_returns_fallback_when_no_relevant_documents(monkeypatch):
    def fake_answer_with_rag(question: str):
        assert question == "如何制作巧克力蛋糕？"
        return {'answer': '根据现有资料无法回答', 'sources': []}

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={
            "question": "如何制作巧克力蛋糕？",
        }
    )

    assert response.status_code == 200
    assert response.json() == {'answer': '根据现有资料无法回答', 'sources': []}


def test_ai_rag_rejects_missing_question(monkeypatch):
    def fake_answer_with_rag(question: str):
        raise AssertionError(
            "无效问题不应该调用 RAG 服务"
        )

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    response = client.post(
        "/ai/rag",
        json={},
    )

    assert response.status_code == 422


def test_ai_retrieve_returns_search_results(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int = 3,
            min_score: float = 0.5,
    ) -> list[dict]:
        assert question == "什么工具可以管理代码版本？"
        assert top_k == 2
        assert min_score == 0.5

        return [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ]

    monkeypatch.setattr(
        rag_service,
        "search_chunks",
        fake_search_chunks,
    )

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "什么工具可以管理代码版本？",
        "count": 1,
        "data": [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ],
    }


def test_ai_retrieve_returns_empty_data_when_no_results(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int = 3,
            min_score: float = 0.5,
    ) -> list[dict]:
        return []

    monkeypatch.setattr(
        rag_service,
        "search_chunks",
        fake_search_chunks,
    )

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "什么工具可以管理代码版本？",
        "count": 0,
        "data": [],
    }


def test_ai_retrieve_uses_default_top_k_when_omitted(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        assert question == "什么工具可以管理代码版本？"
        assert top_k == 3
        assert min_score == 0.5

        return [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ]

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "什么工具可以管理代码版本？",
        "count": 1,
        "data": [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ],
    }


def test_ai_retrieve_rejects_missing_question(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "top_k": 2,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_rejects_whitespace_only_question(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "   ",
            "top_k": 2,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_rejects_empty_question(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "",
            "top_k": 2,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_strips_surrounding_whitespace(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        assert question == "什么工具可以管理代码版本？"
        assert top_k == 2
        assert min_score == 0.5

        return []

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "  什么工具可以管理代码版本？  \n",
            "top_k": 2,
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "什么工具可以管理代码版本？",
        "count": 0,
        "data": [],
    }


def test_ai_retrieve_rejects_question_longer_than_500_characters(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    longer_question = "问" * 501

    response = client.post(
        "/ai/retrieve",
        json={
            "question": longer_question,
            "top_k": 2,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_accepts_question_with_500_characters(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        assert len(question) == 500

        return [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ]

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    question = "问" * 500

    response = client.post(
        "/ai/retrieve",
        json={
            "question": question,
            "top_k": 2,
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": question,
        "count": 1,
        "data": [
            {
                "rank": 1,
                "source": "git.md",
                "chunk_id": 1,
                "content": "Git 是一个分布式版本控制系统。",
                "score": 0.63,
            }
        ],
    }


def test_ai_retrieve_rejects_top_k_below_minimum(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
            "top_k": 0,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_rejects_top_k_above_maximum(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效问题不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
            "top_k": 11,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_returns_503_when_search_service_fails(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise RuntimeError("模拟检索服务初始化失败")

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)

    response = client.post(
        "/ai/retrieve",
        json={
            "question": "什么工具可以管理代码版本？",
            "top_k": 2,
        }
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "检索服务暂不可用",
    }


def test_ai_retrieve_uses_default_min_score_when_omitted(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        assert question == "怎么使用github仓库管理代码"
        assert top_k == 2
        assert min_score == 0.5
        return []

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)
    response = client.post(
        "/ai/retrieve",
        json={
            "question": "怎么使用github仓库管理代码",
            "top_k": 2,
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "怎么使用github仓库管理代码",
        "count": 0,
        "data": [],
    }


def test_ai_retrieve_passes_custom_min_score(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        assert question == "怎么使用github仓库管理代码"
        assert top_k == 2
        assert min_score == 0.48
        return []

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)
    response = client.post(
        "/ai/retrieve",
        json={
            "question": "怎么使用github仓库管理代码",
            "top_k": 2,
            "min_score": 0.48,
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "怎么使用github仓库管理代码",
        "count": 0,
        "data": [],
    }


def test_ai_retrieve_rejects_min_score_below_zero(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效的 min_score 不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)
    response = client.post(
        "/ai/retrieve",
        json={
            "question": "怎么使用github仓库管理代码",
            "top_k": 2,
            "min_score": -0.48,
        }
    )

    assert response.status_code == 422


def test_ai_retrieve_rejects_min_score_above_one(monkeypatch):
    def fake_search_chunks(
            question: str,
            top_k: int,
            min_score: float,
    ) -> list[dict]:
        raise AssertionError(
            "无效的 min_score 不应该调用检索服务",
        )

    monkeypatch.setattr(rag_service, "search_chunks", fake_search_chunks)
    response = client.post(
        "/ai/retrieve",
        json={
            "question": "怎么使用github仓库管理代码",
            "top_k": 2,
            "min_score": 1.1,
        }
    )

    assert response.status_code == 422


def test_search_limit_101(monkeypatch):
    def fake_search_tasks(keyword, skip, limit):
        raise AssertionError("非法参数不应该调用数据库查询")

    monkeypatch.setattr(
        database,
        "search_tasks",
        fake_search_tasks,
    )


    response = client.get(
        "/search",
        params={
            "keyword": "str",
            "skip": 2,
            "limit": 101,

        }
    )

    assert response.status_code == 422


def test_search_pass(monkeypatch):
    def fake_search_tasks(keyword, skip, limit):
        assert keyword == "str"
        assert skip == 2
        assert limit == 10

        return []

    monkeypatch.setattr(
        database,
        "search_tasks",
        fake_search_tasks,
    )

    response = client.get(
        "/search",
        params={
            "keyword": "str",
            "skip": 2,
            "limit": 10,
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "keyword": "str",
        "skip": 2,
        "limit": 10,
        "data": [],
    }

def test_ai_rag_return_500_when_answer_is_not_str(monkeypatch):
    def fake_answer_with_rag(question: str):
        assert question == "测试"
        return []

    monkeypatch.setattr(rag_service, "answer_with_rag", fake_answer_with_rag)

    # 默认 client：确认抛出的确实是“响应校验错误”
    with pytest.raises(ResponseValidationError):
        client.post("/ai/rag", json={"question": "测试"})

    # client_1：确认客户端最终看到的状态码是 500
    response = client_1.post("/ai/rag", json={"question": "测试"})
    assert response.status_code == 500

