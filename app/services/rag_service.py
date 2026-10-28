import os
from pathlib import Path

import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from app.services import llm_service
from practice.rag_document_practice import load_and_split_documents

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def get_model_path() -> Path:
    model_path_text = os.getenv("EMBEDDING_MODEL_PATH")

    if model_path_text is None or not model_path_text.strip():
        raise RuntimeError("Embedding 模型路径未配置")

    model_path = Path(model_path_text.strip())

    if not model_path.is_dir():
        raise RuntimeError("Embedding 模型目录不存在")

    return model_path


DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "practice" / "documents"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model: SentenceTransformer | None = None
chunks: list[dict] = []
chunk_embeddings = None


def initialize_rag() -> None:
    global model, chunks, chunk_embeddings

    if model is not None and chunks and chunk_embeddings is not None:
        return

    model_path = get_model_path()

    model = SentenceTransformer(
        str(model_path),
        device=str(DEVICE),
    )

    chunks = load_and_split_documents(
        directory_path=DOCUMENTS_DIR,
        chunk_size=50,
        chunk_overlap=10,
    )

    if not chunks:
        raise RuntimeError("没有找到知识库文档")

    contents = []

    for chunk in chunks:
        contents.append(chunk["content"])

    chunk_embeddings = model.encode(contents)


def search_chunks(
        question: str,
        top_k: int = 2,
        min_score: float = 0.5,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    initialize_rag()

    if model is None or chunk_embeddings is None:
        raise RuntimeError("RAG 服务初始化失败")

    question_embeddings = model.encode(
        [question],
        prompt_name="query",
    )

    scores = model.similarity(
        question_embeddings,
        chunk_embeddings,
    )[0]

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
        source = result["source"]
        chunk_id = result["chunk_id"]
        content = result["content"]

        context_part = (
            f"来源：{source}，文本块：{chunk_id}\n"
            f"{content}"
        )

        context_parts.append(context_part)

    return "\n\n".join(context_parts)


def answer_with_rag(question: str, min_score: float = 0.5) -> dict | None:
    results = search_chunks(
        question=question,
        top_k=5,
        min_score=min_score,
    )

    sources = []
    for result in results:
        dic = {
            "source": result["source"],
            "chunk_id": result["chunk_id"],
            "content": result["content"]
        }
        sources.append(dic)

    if not sources:
        return {
            "answer": "根据现有资料无法回答",
            "sources": sources
        }

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
            "content": (
                f"上下文：\n{context}\n\n"
                f"问题：\n{question}"
            ),
        },
    ]

    answer = llm_service.ask_chat(messages)

    if answer is None or not answer.strip():
        return None

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":
    print(answer_with_rag("怎么使用github仓库管理代码", min_score=0.48))
