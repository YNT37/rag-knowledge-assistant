from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )


class AskResponse(BaseModel):
    answer: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(
        min_length=1,
    )


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
    )


class ChatResponse(BaseModel):
    answer: str
    history: list[ChatMessage]
