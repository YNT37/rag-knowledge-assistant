from langchain_core.language_models import FakeListChatModel
from langchain_core.messages import HumanMessage, SystemMessage


def build_rag_messages(question: str, context: str) -> list[SystemMessage | HumanMessage]:
    system_message = SystemMessage(content="只能根据上下文回答；资料不足时回答“根据现有资料无法回答”。")
    human_message = HumanMessage(content=f"上下文：\n{context}\n\n问题：\n{question}")
    return [system_message, human_message]


messages = build_rag_messages(
    question="什么是变量？",
    context="Python通过赋值绑定变量。"
)
print(messages[1].content)


model = FakeListChatModel(responses=["变量是名字与值的绑定。"])
response = model.invoke(messages)
print(response.content)