from fastapi import APIRouter, HTTPException
from openai import APIConnectionError

from app.services import rag_service
from app.schemas.rag_schemas import RagRequest, RagResponse, RetrieveRequest, RetrieveResponse

router = APIRouter(prefix="/ai")


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
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="检索服务暂不可用",
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
