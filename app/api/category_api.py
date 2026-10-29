from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.kb_database import get_kb_session
from app.schemas.kb_schemas import (
    CategoryDeleteResult,
    CategoryInput,
    CategoryItem,
    CategoryList,
)
from app.services import category_service


router = APIRouter(prefix="/categories", tags=["knowledge categories"])
KbSession = Annotated[Session, Depends(get_kb_session)]
CategoryId = Annotated[int, Path(gt=0)]


@router.get("", response_model=CategoryList)
def get_categories(session: KbSession):
    data = category_service.list_categories(session)
    return {"count": len(data), "data": data}


@router.post("", status_code=201, response_model=CategoryItem)
def create_category(request: CategoryInput, session: KbSession):
    return category_service.create_category(session, request.name)


@router.patch("/{category_id}", response_model=CategoryItem)
def rename_category(
    category_id: CategoryId,
    request: CategoryInput,
    session: KbSession,
):
    return category_service.rename_category(session, category_id, request.name)


@router.delete("/{category_id}", response_model=CategoryDeleteResult)
def delete_category(category_id: CategoryId, session: KbSession):
    return category_service.delete_category(session, category_id)
