from pathlib import Path


def read_document(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    return content


def split_document(
    content: str,
    source: str,
    chunk_size: int = 20,
    chunk_overlap: int = 0,
) -> list[dict]:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    chunks = []
    step_size = chunk_size - chunk_overlap

    for chunk_id, start_index in enumerate(
        range(0, len(content), step_size),
        start=1,
    ):
        end_index = start_index + chunk_size
        chunk_text = content[start_index:end_index]

        chunk_record = {
            "source": source,
            "chunk_id": chunk_id,
            "content": chunk_text,
        }

        chunks.append(chunk_record)

    return chunks


def search_chunks(
        chunks: list[dict],
        keyword: str,
) -> list[dict]:
    results = []
    normalized_keyword = keyword.lower()

    for chunk in chunks:
        normalized_content = chunk["content"].lower()

        if normalized_keyword in normalized_content:
            results.append(chunk)

    return results


def load_and_split_documents(
        directory_path: Path,
        chunk_size: int = 20,
        chunk_overlap: int = 0,
) -> list[dict]:
    document_paths = list(directory_path.glob("*.md"))

    all_chunks = []

    for document_path in document_paths:
        document_content = read_document(document_path)

        document_chunks = split_document(
            content=document_content,
            source=document_path.name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        all_chunks.extend(document_chunks)

    return all_chunks


def count_chunks_by_source(chunks: list[dict]) -> dict[str, int]:
    source_counts = {}
    for chunk in chunks:
        source = chunk["source"]
        if source not in source_counts:
            source_counts[source] = 1
        else:
            source_counts[source] += 1

    return source_counts


if __name__ == "__main__":
    chunks = [
        {
            "source": "fastapi.md",
            "chunk_id": 1,
            "content": "FastAPI 是 Web 框架",
        },
        {
            "source": "sqlite.md",
            "chunk_id": 1,
            "content": "SQLite 是数据库",
        },
        {
            "source": "fastapi.md",
            "chunk_id": 2,
            "content": "FastAPI 支持路由",
        },
    ]

    print(count_chunks_by_source(chunks))
    print(count_chunks_by_source([]))