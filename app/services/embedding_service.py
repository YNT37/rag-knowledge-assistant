import os

from openai import OpenAI, OpenAIError


def select_embedding_backend(value: str | None) -> str:
    if value is None:
        return "local"

    if value == "local" or value == "siliconflow":
        return value

    raise RuntimeError("提示向量模式配置不支持")


def get_embedding_backend() -> str:
    backend = os.getenv("EMBEDDING_BACKEND")
    return select_embedding_backend(backend)


def create_embedding_client(api_key: str, base_url: str) -> OpenAI:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return client


def embed_cloud_text(client, text: str, model: str) -> list[float]:
    try:
        response = client.embeddings.create(
            input=text,
            model=model,
            encoding_format="float",
        )
    except OpenAIError:
        raise RuntimeError("云端向量服务暂不可用") from None
    try:
        vector = response.data[0].embedding
    except (AttributeError, IndexError, TypeError):
        raise RuntimeError("云端向量服务返回无效结果") from None
    if not isinstance(vector, list) or not vector:
        raise RuntimeError("云端向量服务返回无效结果")
    return vector


def get_siliconflow_config() -> tuple[str, str, str]:
    api_key = os.getenv("EMBEDDING_API_KEY")
    base_url = os.getenv("EMBEDDING_BASE_URL")
    model = os.getenv("EMBEDDING_MODEL")

    if not api_key:
        raise RuntimeError("缺少配置：EMBEDDING_API_KEY")
    if not base_url:
        raise RuntimeError("缺少配置：EMBEDDING_BASE_URL")
    if not model:
        raise RuntimeError("缺少配置：EMBEDDING_MODEL")

    return api_key, base_url, model


def create_siliconflow_client() -> tuple[OpenAI, str]:
    api_key, base_url, model = get_siliconflow_config()
    return create_embedding_client(api_key, base_url), model
