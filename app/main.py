import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api import category_api, chat_api, document_api, rag_api, task_api
from app.core import database
from app.core.kb_database import DOCUMENTS_DIR, engine
from app.services.document_service import recover_document_storage


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    with Session(engine) as session:
        recovery = recover_document_storage(session, DOCUMENTS_DIR)
        if recovery["problems"]:
            logger.warning("知识库正文恢复检查发现问题：%s", recovery["problems"])
    yield


app = FastAPI(
    title="技术资料知识库",
    description="单用户资料分类、导入、检索问答与引用。",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(task_api.router)
app.include_router(chat_api.router)
app.include_router(rag_api.router)
app.include_router(category_api.router)
app.include_router(document_api.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:63342",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()


@app.get("/")
async def root():
    return {"msg": "Hello World"}
