from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import category_api, document_api
from app.core import kb_state
from app.core.kb_database import get_kb_session
from app.models.kb_models import Base, Category, Document
from app.schemas.kb_schemas import CategoryInput, DocumentCreateInput
from app.services import category_service, document_service, rag_service


def _compare_text(left: str, right: str) -> int:
    normalized_left = left.casefold()
    normalized_right = right.casefold()
    return (normalized_left > normalized_right) - (
        normalized_left < normalized_right
    )


@pytest.fixture()
def kb_store(tmp_path: Path):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(dbapi_connection, _):
        dbapi_connection.create_collation(
            "utf8mb4_0900_as_ci",
            _compare_text,
        )
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    with session_factory.begin() as session:
        session.add(Category(name="未分类", is_default=True))

    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()
    kb_state.index_dirty = True
    yield {
        "engine": engine,
        "session_factory": session_factory,
        "documents_dir": documents_dir,
    }
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_p0_routes_are_registered():
    category_routes = {
        (route.path, frozenset(route.methods or set()))
        for route in category_api.router.routes
    }
    document_routes = {
        (route.path, frozenset(route.methods or set()))
        for route in document_api.router.routes
    }
    assert ("/categories", frozenset({"GET"})) in category_routes
    assert ("/categories", frozenset({"POST"})) in category_routes
    assert ("/categories/{category_id}", frozenset({"PATCH"})) in category_routes
    assert ("/categories/{category_id}", frozenset({"DELETE"})) in category_routes
    assert ("/documents", frozenset({"GET"})) in document_routes
    assert ("/documents", frozenset({"POST"})) in document_routes
    assert ("/documents/{source}", frozenset({"GET"})) in document_routes
    assert ("/documents/{source}", frozenset({"DELETE"})) in document_routes
    assert ("/documents/{source}/category", frozenset({"PATCH"})) in document_routes


def test_p0_http_flow(kb_store, monkeypatch: pytest.MonkeyPatch):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    monkeypatch.setattr(document_api, "DOCUMENTS_DIR", documents_dir)

    def isolated_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app = FastAPI()
    app.include_router(category_api.router)
    app.include_router(document_api.router)
    app.dependency_overrides[get_kb_session] = isolated_session

    with TestClient(app) as client:
        category = client.post("/categories", json={"name": "HTTP验收"})
        assert category.status_code == 201
        imported = client.post(
            "/documents",
            json={
                "source": "http-flow.md",
                "content": "通过 HTTP 导入的正文",
                "category_id": category.json()["id"],
            },
        )
        assert imported.status_code == 201
        listing = client.get(
            "/documents",
            params={"category_id": category.json()["id"]},
        )
        assert listing.status_code == 200
        assert listing.json()["data"][0]["source"] == "http-flow.md"
        assert client.get("/documents/http-flow.md").status_code == 200
        assert client.delete("/documents/http-flow.md").status_code == 200
        invalid = client.post(
            "/documents",
            json={"source": "../escape.md", "content": "正文"},
        )
        assert invalid.status_code == 422


def test_category_crud_and_default_protection(kb_store):
    session_factory = kb_store["session_factory"]
    with session_factory() as session:
        assert category_service.list_categories(session) == [
            {
                "id": 1,
                "name": "未分类",
                "is_default": True,
                "document_count": 0,
            }
        ]
    with session_factory() as session:
        created = category_service.create_category(session, " 后端 ")
    assert created["name"] == "后端"
    category_id = created["id"]

    with session_factory() as session:
        renamed = category_service.rename_category(session, category_id, "Python")
    assert renamed["name"] == "Python"

    with session_factory() as session, pytest.raises(HTTPException) as duplicate:
        category_service.create_category(session, "Python")
    assert duplicate.value.status_code == 409

    with session_factory() as session, pytest.raises(HTTPException) as protected:
        category_service.delete_category(session, 1)
    assert protected.value.status_code == 409

    with pytest.raises(ValidationError):
        CategoryInput(name="未分类")


def test_document_import_list_detail_move_and_delete(kb_store):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    with session_factory() as session:
        category = category_service.create_category(session, "FastAPI")
    with session_factory() as session:
        imported = document_service.import_document(
            session,
            documents_dir,
            "fastapi.md",
            "# FastAPI\n\n依赖注入用于复用请求相关逻辑。",
            category["id"],
        )
    assert imported["category_name"] == "FastAPI"
    assert (documents_dir / "fastapi.md").read_text(encoding="utf-8").startswith(
        "# FastAPI"
    )
    assert kb_state.index_dirty is True

    with session_factory() as session:
        listing = document_service.list_documents(session, category["id"])
    assert len(listing) == 1
    assert listing[0]["source"] == "fastapi.md"

    with session_factory() as session:
        detail = document_service.get_document(session, documents_dir, "fastapi.md")
    assert detail["char_count"] == len(detail["content"])

    with session_factory() as session:
        moved = document_service.move_document(session, "fastapi.md", 1)
    assert moved["category_name"] == "未分类"

    with session_factory() as session:
        deleted = document_service.delete_document(
            session,
            documents_dir,
            "fastapi.md",
        )
    assert deleted == {"source": "fastapi.md", "deleted": True}
    assert not (documents_dir / "fastapi.md").exists()
    with session_factory() as session, pytest.raises(HTTPException) as missing:
        document_service.get_document(session, documents_dir, "fastapi.md")
    assert missing.value.status_code == 404


def test_delete_category_moves_documents_to_default(kb_store):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    with session_factory() as session:
        category_id = category_service.create_category(session, "待整理")["id"]
    with session_factory() as session:
        document_service.import_document(
            session,
            documents_dir,
            "move-me.md",
            "待整理资料",
            category_id,
        )
    with session_factory() as session:
        deleted = category_service.delete_category(session, category_id)
    assert deleted["moved_count"] == 1
    assert deleted["target_category_id"] == 1
    with session_factory() as session:
        detail = document_service.get_document(session, documents_dir, "move-me.md")
    assert detail["category_name"] == "未分类"


@pytest.mark.parametrize(
    "source",
    ["../escape.md", "folder/note.md", "UPPER.MD", "CON.md"],
)
def test_document_import_rejects_unsafe_source(kb_store, source: str):
    with pytest.raises(ValidationError):
        DocumentCreateInput(source=source, content="正文", category_id=None)
    assert not list(kb_store["documents_dir"].glob("*.md"))


def test_duplicate_file_and_missing_category_do_not_leave_files(kb_store):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    with session_factory() as session:
        document_service.import_document(
            session,
            documents_dir,
            "same.md",
            "正文",
        )
    with session_factory() as session, pytest.raises(HTTPException) as duplicate:
        document_service.import_document(
            session,
            documents_dir,
            "same.md",
            "新正文",
        )
    assert duplicate.value.status_code == 409
    assert (documents_dir / "same.md").read_text(encoding="utf-8") == "正文"

    with session_factory() as session, pytest.raises(HTTPException) as missing:
        document_service.import_document(
            session,
            documents_dir,
            "orphan.md",
            "正文",
            999,
        )
    assert missing.value.status_code == 404
    assert not (documents_dir / "orphan.md").exists()


def test_restart_recovery_restores_pending_file(kb_store):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    with session_factory() as session:
        document_service.import_document(
            session,
            documents_dir,
            "recover.md",
            "可恢复正文",
        )
    with session_factory() as session:
        document_id = session.scalar(
            select(Document.id).where(Document.source == "recover.md")
        )
    trash = documents_dir / ".trash"
    trash.mkdir()
    pending = trash / f"{document_id}.{'a' * 32}.pending"
    (documents_dir / "recover.md").rename(pending)

    with session_factory() as session:
        recovery = document_service.recover_document_storage(
            session,
            documents_dir,
        )
    assert recovery == {"restored": 1, "cleaned": 0, "problems": []}
    assert (documents_dir / "recover.md").read_text(encoding="utf-8") == "可恢复正文"
    assert not pending.exists()


def test_rag_loads_only_registered_documents(kb_store, monkeypatch: pytest.MonkeyPatch):
    session_factory = kb_store["session_factory"]
    documents_dir: Path = kb_store["documents_dir"]
    with session_factory() as session:
        document_service.import_document(
            session,
            documents_dir,
            "registered.md",
            "已登记资料内容",
        )
    (documents_dir / "unregistered.md").write_text("不应进入检索", encoding="utf-8")

    monkeypatch.setattr(rag_service, "engine", kb_store["engine"])
    monkeypatch.setattr(rag_service, "DOCUMENTS_DIR", documents_dir)
    loaded = rag_service._load_registered_chunks()
    assert {item["source"] for item in loaded} == {"registered.md"}

