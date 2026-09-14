import os

from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": "你是一名耐心的 Python 老师，请简短回答"},
    ]

    while True:
        question = input("请输入你的问题（如需退出，请输入”exit“）:")

        if question == "exit":
            print("聊天已结束")
            break

        messages.append({
            "role": "user",
            "content": question,
        })

        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        answer = response.choices[0].message.content
        print("模型回答：", answer)

        messages.append({
            "role": "assistant",
            "content": answer,
        })


if __name__ == "__main__":
    main()
