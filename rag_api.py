from typing import Annotated

from fastapi import APIRouter, HTTPException
from openai import APIConnectionError
from pydantic import BaseModel, StringConstraints,Field

import rag_service

router = APIRouter(prefix="/ai")


class RagRequest(BaseModel):
    question: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=500,
        )
    ]


class RagSource(BaseModel):
    source: str
    chunk_id: int
    content: str


class RagResponse(BaseModel):
    answer: str
    sources: list[RagSource]


class RetrieveRequest(BaseModel):
    question: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=500,
        )
    ]
    top_k: Annotated[
        int,
        Field(ge=1, le=10),
    ] = 3
    min_score: Annotated[
        float,
        Field(
            ge=0,
            le=1,
        )
    ] = 0.5


class RetrieveItem(BaseModel):
    rank: int
    source: str
    chunk_id: int
    content: str
    score: float


class RetrieveResponse(BaseModel):
    question: str
    count: int
    data: list[RetrieveItem]

@router.post(
    "/rag",
    response_model=RagResponse,
)
def ai_rag(request: RagRequest):
    try:
        response = rag_service.answer_with_rag(request.question)
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="模型服务暂不可用",
        )
    if response is None:
        raise HTTPException(
            status_code=502,
            detail="模型未返回有效回答",
        )

    return response


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
)
def ai_retrieve(request: RetrieveRequest):
    try:
        results = rag_service.search_chunks(
            question=request.question,
            top_k=request.top_k,
            min_score=request.min_score,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="检索服务暂不可用",
        )

    count = len(results)

    return {
        "question": request.question,
        "count": count,
        "data": results,
    }
