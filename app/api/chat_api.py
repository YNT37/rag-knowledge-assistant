from fastapi import APIRouter, HTTPException
from openai import APIConnectionError

from app.services import llm_service
from app.schemas.chat_schemas import AskRequest, AskResponse, ChatMessage, ChatRequest, ChatResponse

router = APIRouter()


@router.post(
    "/ai/ask",
    response_model=AskResponse,
)
def ai_question(request: AskRequest):
    if (
            not llm_service.api_key
            or not llm_service.base_url
            or not llm_service.model
    ):
        raise HTTPException(
            status_code=503,
            detail="模型服务未配置",
        )

    try:
        answer = llm_service.ask_llm(request.question)
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="模型服务暂不可用",
        )

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="模型未返回有效回答",
        )

    return {"answer": answer}


def build_chat_messages(request: ChatRequest) -> list[dict[str, str]]:
    messages = [
        {
            "role": "system",
            "content": "你是一名耐心的 Python 老师。",
        }
    ]

    for previous in request.history:
        messages.append({
            "role": previous.role,
            "content": previous.content,
        })

    messages.append({
        "role": "user",
        "content": request.question,
    })

    return messages


@router.post(
    "/ai/chat",
    response_model=ChatResponse,
)
def ai_chat(request: ChatRequest):
    if (
            not llm_service.api_key
            or not llm_service.base_url
            or not llm_service.model
    ):
        raise HTTPException(
            status_code=503,
            detail="模型服务未配置",
        )

    messages = build_chat_messages(request)

    try:
        answer = llm_service.ask_chat(messages)
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="模型服务暂不可用",
        )

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="模型未返回有效回答",
        )

    updated_history = list(request.history)
    updated_history.append(ChatMessage(role="user", content=request.question))
    updated_history.append(ChatMessage(role="assistant", content=answer))

    return {
        "answer": answer,
        "history": updated_history,
    }
