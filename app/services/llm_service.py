import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

def ask_llm(question: str):
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model = model,
        messages=[
            {"role": "system", "content": "你是一名耐心的 Python 老师。请用不超过三句话回答初学者，先解释概念，再给一个简短例子；不要使用标题、表格或代码块。"},
            {"role": "user", "content": question},
        ]
    )

    return response.choices[0].message.content


def ask_chat(messages: list[dict[str, str]]) -> str | None:
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model = model,
        messages = messages,
    )

    return response.choices[0].message.content
