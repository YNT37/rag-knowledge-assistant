from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import kb_state
from app.core.kb_validation import normalize_category_name
from app.models.kb_models import Category, Document


def require_default(session: Session) -> Category:
    rows = session.scalars(
        select(Category).where(Category.is_default.is_(True))
    ).all()
    if len(rows) != 1 or rows[0].name != "未分类":
        raise HTTPException(503, "默认分类异常，请先运行初始化脚本")
    return rows[0]


def category_item(session: Session, category: Category) -> dict:
    count = session.scalar(
        select(func.count(Document.id)).where(Document.category_id == category.id)
    )
    return {
        "id": category.id,
        "name": category.name,
        "is_default": category.is_default,
        "document_count": count or 0,
    }


def list_categories(session: Session) -> list[dict]:
    with kb_state.OP_LOCK:
        statement = (
            select(Category, func.count(Document.id))
            .outerjoin(Document, Document.category_id == Category.id)
            .group_by(Category.id, Category.name, Category.is_default)
            .order_by(Category.id)
        )
        return [
            {
                "id": category.id,
                "name": category.name,
                "is_default": category.is_default,
                "document_count": count,
            }
            for category, count in session.execute(statement).all()
        ]


def create_category(session: Session, name: str) -> dict:
    name = normalize_category_name(name)
    try:
        with kb_state.OP_LOCK:
            with session.begin():
                duplicate = session.scalar(
                    select(Category).where(Category.name == name)
                )
                if duplicate is not None:
                    raise HTTPException(409, "分类名已存在")
                category = Category(name=name, is_default=False)
                session.add(category)
                session.flush()
                result = category_item(session, category)
            return result
    except IntegrityError as exc:
        raise HTTPException(409, "分类名已存在") from exc


def rename_category(session: Session, category_id: int, name: str) -> dict:
    name = normalize_category_name(name)
    try:
        with kb_state.OP_LOCK:
            with session.begin():
                category = session.get(Category, category_id)
                if category is None:
                    raise HTTPException(404, "分类不存在")
                if category.is_default:
                    raise HTTPException(409, "不能修改未分类")
                duplicate = session.scalar(
                    select(Category).where(
                        Category.name == name,
                        Category.id != category_id,
                    )
                )
                if duplicate is not None:
                    raise HTTPException(409, "分类名已存在")
                category.name = name
                session.flush()
                result = category_item(session, category)
            return result
    except IntegrityError as exc:
        raise HTTPException(409, "分类名已存在") from exc


def delete_category(session: Session, category_id: int) -> dict:
    with kb_state.OP_LOCK:
        with session.begin():
            category = session.get(Category, category_id)
            if category is None:
                raise HTTPException(404, "分类不存在")
            if category.is_default:
                raise HTTPException(409, "不能删除未分类")

            default = require_default(session)
            result = session.execute(
                update(Document)
                .where(Document.category_id == category.id)
                .values(category_id=default.id)
            )
            moved_count = result.rowcount or 0
            session.delete(category)
            session.flush()
            return {
                "deleted_category_id": category_id,
                "moved_count": moved_count,
                "target_category_id": default.id,
            }
