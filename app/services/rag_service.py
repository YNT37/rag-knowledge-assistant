import logging
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import kb_state
from app.core.kb_database import DOCUMENTS_DIR, engine
from app.core.kb_validation import get_document_path
from app.models.kb_models import Document
from app.services import llm_service
from practice.rag_document_practice import split_document


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


# 继承Uvicorn的控制台handler和INFO级别，使分阶段计时可见。
logger = logging.getLogger("uvicorn.error.rag")


def _positive_int_setting(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name}必须是整数") from exc
    if value <= 0:
        raise RuntimeError(f"{name}必须大于0")
    return value


RAG_CHUNK_SIZE = _positive_int_setting("RAG_CHUNK_SIZE", 400)
RAG_CHUNK_OVERLAP = _positive_int_setting("RAG_CHUNK_OVERLAP", 80)
if RAG_CHUNK_OVERLAP >= RAG_CHUNK_SIZE:
    raise RuntimeError("RAG_CHUNK_OVERLAP必须小于RAG_CHUNK_SIZE")


def get_model_path() -> Path:
    model_path_text = os.getenv("EMBEDDING_MODEL_PATH")
    if model_path_text is None or not model_path_text.strip():
        raise RuntimeError("Embedding 模型路径未配置")

    model_path = Path(model_path_text.strip())
    if not model_path.is_dir():
        raise RuntimeError("Embedding 模型目录不存在")
    return model_path


model: Any | None = None
chunks: list[dict] = []
chunk_embeddings = None


def _load_registered_chunks() -> list[dict]:
    with Session(engine) as session:
        sources = session.scalars(
            select(Document.source).order_by(Document.id)
        ).all()

    loaded: list[dict] = []
    for source in sources:
        try:
            path = get_document_path(DOCUMENTS_DIR, source)
            content = path.read_text(encoding="utf-8")
        except (OSError, ValueError, UnicodeError) as exc:
            raise RuntimeError(f"知识库正文不可用：{source}") from exc
        loaded.extend(
            split_document(
                content=content,
                source=source,
                chunk_size=RAG_CHUNK_SIZE,
                chunk_overlap=RAG_CHUNK_OVERLAP,
            )
        )
    return loaded


def initialize_rag() -> None:
    global model, chunks, chunk_embeddings

    with kb_state.OP_LOCK:
        if not kb_state.index_dirty:
            return

        started_at = time.perf_counter()
        rebuilt_chunks = _load_registered_chunks()
        if not rebuilt_chunks:
            chunks = []
            chunk_embeddings = None
            kb_state.index_dirty = False
            logger.info("RAG索引为空：没有已登记资料")
            return

        active_model = model
        if active_model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            active_model = SentenceTransformer(
                str(get_model_path()),
                device=device,
                model_kwargs=(
                    {"torch_dtype": torch.float32}
                    if device == "cpu"
                    else None
                ),
            )

        contents = [chunk["content"] for chunk in rebuilt_chunks]
        rebuilt_embeddings = active_model.encode(
            contents,
            batch_size=32,
            show_progress_bar=False,
        )

        model = active_model
        chunks = rebuilt_chunks
        chunk_embeddings = rebuilt_embeddings
        kb_state.index_dirty = False
        logger.info(
            "RAG索引重建完成：chunks=%d, chunk_size=%d, overlap=%d, "
            "device=%s, elapsed=%.2fs",
            len(rebuilt_chunks),
            RAG_CHUNK_SIZE,
            RAG_CHUNK_OVERLAP,
            getattr(active_model, "device", "unknown"),
            time.perf_counter() - started_at,
        )


def search_chunks(
    question: str,
    top_k: int = 2,
    min_score: float = 0.5,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    initialize_rag()
    with kb_state.OP_LOCK:
        if not chunks:
            return []
        if model is None or chunk_embeddings is None:
            raise RuntimeError("RAG 服务初始化失败")

        question_embeddings = model.encode([question], prompt_name="query")
        scores = model.similarity(question_embeddings, chunk_embeddings)[0]
        actual_top_k = min(top_k, len(chunks))
        top_scores, top_indices = scores.topk(k=actual_top_k)

        results = []
        for rank in range(actual_top_k):
            chunk_index = top_indices[rank].item()
            score = top_scores[rank].item()
            if score >= min_score:
                chunk = chunks[chunk_index]
                results.append({
                    "rank": rank + 1,
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "score": score,
                })
        return results


def build_context(results: list[dict]) -> str:
    context_parts = []
    for result in results:
        context_parts.append(
            f"来源：{result['source']}，文本块：{result['chunk_id']}\n"
            f"{result['content']}"
        )
    return "\n\n".join(context_parts)


def answer_with_rag(question: str, min_score: float = 0.5) -> dict | None:
    started_at = time.perf_counter()
    results = search_chunks(question=question, top_k=5, min_score=min_score)
    retrieval_elapsed = time.perf_counter() - started_at
    sources = [
        {
            "source": result["source"],
            "chunk_id": result["chunk_id"],
            "content": result["content"],
        }
        for result in results
    ]
    if not sources:
        logger.info(
            "RAG问答无可用片段：retrieval=%.2fs",
            retrieval_elapsed,
        )
        return {"answer": "根据现有资料无法回答", "sources": []}

    context = build_context(sources)
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个知识库问答助手。"
                "只能根据提供的上下文回答问题。"
                "如果上下文中没有答案，请回答“根据现有资料无法回答”。"
                "回答时请注明来源文件。"
            ),
        },
        {
            "role": "user",
            "content": f"上下文：\n{context}\n\n问题：\n{question}",
        },
    ]
    generation_started_at = time.perf_counter()
    answer = llm_service.ask_chat(messages)
    generation_elapsed = time.perf_counter() - generation_started_at
    logger.info(
        "RAG问答完成：sources=%d, retrieval=%.2fs, generation=%.2fs, "
        "total=%.2fs",
        len(sources),
        retrieval_elapsed,
        generation_elapsed,
        time.perf_counter() - started_at,
    )
    if answer is None or not answer.strip():
        return None
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    print(answer_with_rag("怎么使用github仓库管理代码", min_score=0.48))
