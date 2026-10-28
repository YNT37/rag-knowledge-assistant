from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


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
