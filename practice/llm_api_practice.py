import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")


print("API 密钥是否读取成功：", api_key is not None)
print("服务地址：", base_url)
print("模型名称：", model)

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

question = input("请输入问题：")

response = client.chat.completions.create(
    model = model,
    messages=[
        {"role":"system", "content": "你是一名耐心的 Python 老师。"},
        {"role":"user", "content": question},
    ]
)

answer = response.choices[0].message.content

print("模型回答", answer)