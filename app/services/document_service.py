import logging
import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import kb_state
from app.core.kb_validation import get_document_path, normalize_source
from app.models.kb_models import Category, Document
from app.services.category_service import require_default


logger = logging.getLogger(__name__)


def _source_or_422(source: str) -> str:
    try:
        return normalize_source(source)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def document_item(document: Document, category: Category) -> dict:
    return {
        "id": document.id,
        "source": document.source,
        "category_id": category.id,
        "category_name": category.name,
    }


def require_document(session: Session, source: str) -> tuple[Document, Category]:
    source = _source_or_422(source)
    row = session.execute(
        select(Document, Category)
        .join(Category, Document.category_id == Category.id)
        .where(Document.source == source)
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "资料不存在")
    return row[0], row[1]


def require_category(session: Session, category_id: int | None) -> Category:
    if category_id is None:
        return require_default(session)
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(404, "目标分类不存在")
    return category


def list_documents(
    session: Session,
    category_id: int | None = None,
) -> list[dict]:
    with kb_state.OP_LOCK:
        if category_id is not None and session.get(Category, category_id) is None:
            raise HTTPException(404, "分类不存在")
        statement = (
            select(Document, Category)
            .join(Category, Document.category_id == Category.id)
            .order_by(Document.id)
        )
        if category_id is not None:
            statement = statement.where(Document.category_id == category_id)
        return [
            document_item(document, category)
            for document, category in session.execute(statement).all()
        ]


def get_document(session: Session, directory_path: Path, source: str) -> dict:
    with kb_state.OP_LOCK:
        document, category = require_document(session, source)
        try:
            path = get_document_path(directory_path, document.source)
            with path.open("r", encoding="utf-8", newline="") as stream:
                content = stream.read()
        except (OSError, ValueError, UnicodeError) as exc:
            raise HTTPException(503, "正文缺失、不可读或路径异常") from exc
        return {
            **document_item(document, category),
            "content": content,
            "char_count": len(content),
        }


def _fresh_document(session: Session, document_id: int) -> tuple[int, str] | None:
    with Session(session.get_bind()) as check:
        row = check.execute(
            select(Document.id, Document.source).where(Document.id == document_id)
        ).one_or_none()
        return None if row is None else (row[0], row[1])


def import_document(
    session: Session,
    directory_path: Path,
    source: str,
    content: str,
    category_id: int | None = None,
) -> dict:
    source = _source_or_422(source)
    if not content.strip() or len(content) > 20000:
        raise HTTPException(422, "正文须非空且不超过20000字符")

    with kb_state.OP_LOCK:
        owned_path: Path | None = None
        document_id: int | None = None
        result: dict | None = None
        commit_started = False
        try:
            with session.begin():
                duplicate = session.scalar(
                    select(Document).where(Document.source == source)
                )
                if duplicate is not None:
                    raise HTTPException(409, "资料名已存在")
                category = require_category(session, category_id)
                path = get_document_path(directory_path, source)
                if path.exists():
                    raise HTTPException(409, "同名正文已存在，请先核对")

                document = Document(source=source, category_id=category.id)
                session.add(document)
                session.flush()
                document_id = document.id
                with path.open("x", encoding="utf-8", newline="") as stream:
                    owned_path = path
                    stream.write(content)
                result = document_item(document, category)
                commit_started = True
        except Exception as exc:
            if commit_started and document_id is not None:
                kb_state.invalidate_rag_index()
                try:
                    persisted = _fresh_document(session, document_id)
                except Exception as check_exc:
                    raise HTTPException(
                        503, "保存结果暂无法确认，保留正文待核对"
                    ) from check_exc
                if persisted == (document_id, source) and result is not None:
                    return result
                if persisted is not None:
                    raise HTTPException(503, "保存记录冲突，保留正文待核对") from exc

            if owned_path is not None:
                try:
                    owned_path.unlink(missing_ok=True)
                except OSError as cleanup_exc:
                    raise HTTPException(
                        503, "保存失败，孤立正文待人工核对"
                    ) from cleanup_exc
            if isinstance(exc, HTTPException):
                raise
            if isinstance(exc, FileExistsError):
                raise HTTPException(409, "同名正文已存在") from exc
            if isinstance(exc, IntegrityError):
                raise HTTPException(409, "资料名已存在") from exc
            logger.exception("资料导入失败")
            raise HTTPException(503, "资料保存失败") from exc

        kb_state.invalidate_rag_index()
        if result is None:
            raise HTTPException(503, "资料保存结果异常")
        return result


def move_document(
    session: Session,
    source: str,
    category_id: int,
) -> dict:
    with kb_state.OP_LOCK:
        with session.begin():
            document, _ = require_document(session, source)
            target = require_category(session, category_id)
            document.category_id = target.id
            session.flush()
            return document_item(document, target)


def _trash_directory(directory_path: Path) -> Path:
    if directory_path.is_symlink() or directory_path.is_junction():
        raise ValueError("正文根目录不能是链接")
    root = directory_path.resolve(strict=True)
    trash = root / ".trash"
    if trash.is_symlink() or trash.is_junction():
        raise ValueError("暂存目录不能是链接")
    trash.mkdir(exist_ok=True)
    if not trash.is_dir() or trash.resolve().parent != root:
        raise ValueError("暂存目录异常")
    return trash


def delete_document(session: Session, directory_path: Path, source: str) -> dict:
    with kb_state.OP_LOCK:
        backup: Path | None = None
        original: Path | None = None
        document_id: int | None = None
        actual_source = ""
        commit_started = False
        try:
            with session.begin():
                document, _ = require_document(session, source)
                document_id = document.id
                actual_source = document.source
                original = get_document_path(directory_path, actual_source)
                if not original.is_file():
                    raise HTTPException(503, "登记存在但正文缺失")
                trash = _trash_directory(directory_path)
                backup = trash / f"{document_id}.{uuid4().hex}.pending"
                original.rename(backup)
                session.delete(document)
                session.flush()
                commit_started = True
        except Exception as exc:
            committed = False
            if commit_started and document_id is not None:
                kb_state.invalidate_rag_index()
                try:
                    persisted = _fresh_document(session, document_id)
                except Exception as check_exc:
                    raise HTTPException(
                        503, "删除结果暂无法确认，暂存待恢复"
                    ) from check_exc
                committed = persisted is None
                if persisted is not None and persisted != (
                    document_id,
                    actual_source,
                ):
                    raise HTTPException(503, "删除记录冲突，暂存待核对") from exc

            if not committed:
                if backup is not None and backup.exists() and original is not None:
                    try:
                        if original.exists():
                            raise OSError("原位置已有文件，不能覆盖恢复")
                        backup.rename(original)
                    except OSError as restore_exc:
                        raise HTTPException(
                            503, "删除未完成，暂存正文待恢复"
                        ) from restore_exc
                if isinstance(exc, HTTPException):
                    raise
                logger.exception("资料删除未完成")
                raise HTTPException(503, "删除失败，资料未确认移除") from exc

        kb_state.invalidate_rag_index()
        if backup is not None:
            try:
                backup.unlink(missing_ok=True)
            except OSError:
                logger.exception("删除已提交，暂存清理待重试")
        return {"source": actual_source, "deleted": True}


def recover_document_storage(session: Session, directory_path: Path) -> dict:
    with kb_state.OP_LOCK:
        records = {
            document.id: document.source
            for document in session.scalars(select(Document)).all()
        }
        result: dict[str, int | list[str]] = {
            "restored": 0,
            "cleaned": 0,
            "problems": [],
        }
        problems = result["problems"]
        if not isinstance(problems, list):
            raise RuntimeError("恢复结果初始化失败")

        trash = _trash_directory(directory_path)
        for item in sorted(trash.iterdir()):
            match = re.fullmatch(r"([1-9][0-9]*)\.[0-9a-f]{32}\.pending", item.name)
            if (
                match is None
                or item.is_symlink()
                or item.is_junction()
                or not item.is_file()
            ):
                problems.append(f"未知暂存项：{item.name}")
                continue
            document_id = int(match.group(1))
            try:
                if document_id not in records:
                    item.unlink()
                    result["cleaned"] = int(result["cleaned"]) + 1
                else:
                    target = get_document_path(directory_path, records[document_id])
                    if target.exists():
                        raise ValueError("原文件与暂存同时存在，需人工核对")
                    item.rename(target)
                    result["restored"] = int(result["restored"]) + 1
            except (OSError, ValueError) as exc:
                problems.append(f"暂存{item.name}：{type(exc).__name__}")

        for source in records.values():
            try:
                path = get_document_path(directory_path, source)
                with path.open("r", encoding="utf-8", newline="") as stream:
                    stream.read()
            except (OSError, ValueError, UnicodeError):
                problems.append(f"正文不可用：{source}")

        kb_state.invalidate_rag_index()
        return result
