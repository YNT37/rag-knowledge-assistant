from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat_api, rag_api, task_api
from app.core import database


app = FastAPI(
    title="FastAPI 任务练习",
    description="用于学习路由、参数校验、请求体、响应模型和 CRUD。",
    version="0.1.0",
)

app.include_router(task_api.router)
app.include_router(chat_api.router)
app.include_router(rag_api.router)
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
