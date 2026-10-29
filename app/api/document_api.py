from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.kb_database import DOCUMENTS_DIR, get_kb_session
from app.schemas.kb_schemas import (
    DocumentCreateInput,
    DocumentDeleteResult,
    DocumentDetail,
    DocumentItem,
    DocumentList,
    DocumentMoveInput,
)
from app.services import document_service


router = APIRouter(prefix="/documents", tags=["knowledge documents"])
KbSession = Annotated[Session, Depends(get_kb_session)]
SourcePath = Annotated[str, Path(min_length=1, max_length=100)]


@router.get("", response_model=DocumentList)
def get_documents(
    session: KbSession,
    category_id: Annotated[int | None, Query(gt=0)] = None,
):
    data = document_service.list_documents(session, category_id)
    return {"count": len(data), "data": data}


@router.post("", status_code=201, response_model=DocumentItem)
def create_document(request: DocumentCreateInput, session: KbSession):
    return document_service.import_document(
        session=session,
        directory_path=DOCUMENTS_DIR,
        source=request.source,
        content=request.content,
        category_id=request.category_id,
    )


@router.get("/{source}", response_model=DocumentDetail)
def get_document(source: SourcePath, session: KbSession):
    return document_service.get_document(session, DOCUMENTS_DIR, source)


@router.patch("/{source}/category", response_model=DocumentItem)
def move_document(
    source: SourcePath,
    request: DocumentMoveInput,
    session: KbSession,
):
    return document_service.move_document(
        session,
        source,
        request.category_id,
    )


@router.delete("/{source}", response_model=DocumentDeleteResult)
def delete_document(source: SourcePath, session: KbSession):
    return document_service.delete_document(session, DOCUMENTS_DIR, source)
