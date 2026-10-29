from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kb_database import DOCUMENTS_DIR, engine
from app.core.kb_validation import get_document_path, normalize_source
from app.models.kb_models import Base, Category, Document
from app.services.document_service import recover_document_storage


def init_kb_schema() -> None:
    Base.metadata.create_all(engine)


def ensure_default_category(session: Session) -> Category:
    # 调用方已经开启事务；辅助函数不自行commit。
    defaults = session.scalars(
        select(Category).where(Category.is_default.is_(True))
    ).all()
    if len(defaults) > 1:
        raise RuntimeError("存在多条默认分类，请先核对数据")
    if defaults:
        if defaults[0].name != "未分类":
            raise RuntimeError("默认分类名称与约定不一致")
        return defaults[0]
    same_name = session.scalar(
        select(Category).where(Category.name == "未分类")
    )
    if same_name is not None:
        raise RuntimeError("未分类名称被普通分类占用，请先核对")
    category = Category(name="未分类", is_default=True)
    session.add(category)
    session.flush()
    return category


def register_existing_documents(
    session: Session,
    directory_path: Path,
) -> dict[str, int]:
    default = ensure_default_category(session)
    if not directory_path.is_dir():
        raise RuntimeError("旧资料目录不存在")

    registered = 0
    skipped = 0
    for file in sorted(directory_path.glob("*.md"), key=lambda path: path.name):
        source = normalize_source(file.name)
        if source != file.name:
            raise RuntimeError(f"旧文件名需人工核对：{file.name}")
        path = get_document_path(directory_path, source)
        if not path.is_file():
            raise RuntimeError(f"非正常Markdown文件：{source}")

        existing = session.scalar(
            select(Document).where(Document.source == source)
        )
        if existing is not None:
            if existing.source != source:
                raise RuntimeError(f"比较规则下存在文件名冲突：{source}")
            skipped += 1
            continue

        session.add(Document(source=source, category_id=default.id))
        session.flush()
        registered += 1

    return {"registered": registered, "skipped": skipped}


if __name__ == "__main__":
    init_kb_schema()
    with Session(engine) as session:
        with session.begin():
            default = ensure_default_category(session)
            default_id = default.id
            registration = register_existing_documents(session, DOCUMENTS_DIR)
    with Session(engine) as session:
        recovery = recover_document_storage(session, DOCUMENTS_DIR)
    print({
        "default_category_id": default_id,
        **registration,
        "recovery": recovery,
    })
