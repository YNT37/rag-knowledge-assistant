import os
from pathlib import Path

import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

import llm_service
from rag_document_practice import load_and_split_documents


load_dotenv()


def get_model_path() -> Path:
    model_path_text = os.getenv("EMBEDDING_MODEL_PATH")

    if model_path_text is None or not model_path_text.strip():
        raise RuntimeError("Embedding 模型路径未配置")

    model_path = Path(model_path_text.strip())

    if not model_path.is_dir():
        raise RuntimeError("Embedding 模型目录不存在")

    return model_path


MODEL_PATH = get_model_path()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DOCUMENTS_DIR = Path(__file__).with_name("documents")

print("开始加载模型")

model = SentenceTransformer(
    str(MODEL_PATH),
    device=DEVICE,
)

print("模型加载成功")
print("运行设备：", model.device)
print("向量维度：", model.get_embedding_dimension())

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

print("文档目录：", DOCUMENTS_DIR)
print("文本块数量：", len(chunks))

for chunk in chunks:
    print(chunk)


def search_chunks(
    question: str,
    top_k: int = 2,
    min_score: float = 0.5,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    question_embeddings = model.encode(
        [question],
        prompt_name="query",
    )

    scores = model.similarity(
        question_embeddings,
        chunk_embeddings,
    )[0]

    actual_top_k = min(top_k, len(chunks))
    top_scores, top_indices = scores.topk(actual_top_k)

    results = []

    for rank in range(actual_top_k):
        chunk_index = top_indices[rank].item()
        score = top_scores[rank].item()

        if score >= min_score:
            chunk = chunks[chunk_index]

            results.append(
                {
                    "rank": rank + 1,
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "score": score,
                }
            )

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


def answer_with_rag(question: str) -> str | None:
    results = search_chunks(
        question=question,
        top_k=2,
        min_score=0.5,
    )

    if not results:
        return "根据现有资料无法回答"

    context = build_context(results)

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

    return answer


if __name__ == "__main__":
    question = "FastAPI 是什么？它有什么作用？"
    answer = answer_with_rag(question)

    if answer is None:
        print("大模型没有返回有效回答")
    else:
        print("回答：")
        print(answer)
