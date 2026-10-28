from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kb_database import DOCUMENTS_DIR, engine
from app.models.kb_models import Base, Category


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


if __name__ == "__main__":
    init_kb_schema()
    with Session(engine) as session:
        with session.begin():
            default = ensure_default_category(session)
            default_id = default.id
    print({"default_category_id": default_id})