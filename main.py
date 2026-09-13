from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from openai import APIConnectionError

import database
import llm_service


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    done: bool | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool


class SearchResponse(BaseModel):
    keyword: str
    limit: int
    skip: int
    data: list[TaskResponse]


class DeleteResponse(BaseModel):
    msg: str
    data: TaskResponse


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )

class AskResponse(BaseModel):
    answer: str

app = FastAPI(
    title="FastAPI 任务练习",
    description="用于学习路由、参数校验、请求体、响应模型和 CRUD。",
    version="0.1.0",
)
database.init_db()


@app.get("/")
async def root():
    return {"msg": "Hello World"}

@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
async def get_tasks():
    return database.get_all_tasks()

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def get_task(task_id: int):
    task = database.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )
    return task


@app.get(
    "/search",
    response_model=SearchResponse,
)
async def search_tasks(
    keyword: Annotated[str, Query(max_length=50)] = "",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    selected_tasks = database.search_tasks(keyword, skip, limit)

    return {
        "keyword": keyword,
        "skip": skip,
        "limit": limit,
        "data": selected_tasks,
    }


@app.post(
    "/tasks",
    status_code=201,
    response_model=TaskResponse,
)
async def create_task(task: TaskCreate):
    new_task = database.create_task(
        task.title,
        task.done,
    )
    return new_task


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task(task_id: int, task: TaskCreate):
    updated_task = database.update_task(
        task_id,
        task.title,
        task.done,
    )

    if updated_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return updated_task


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def partial_update_task(task_id: int, task_update: TaskUpdate):
    updated_task = database.update_task_partial(
        task_id,
        task_update.title,
        task_update.done,
    )
    if updated_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return updated_task


@app.delete(
    "/tasks/{task_id}",
    response_model=DeleteResponse,
)
async def delete_task(task_id: int):
    deleted_task = database.delete_task(task_id)
    if deleted_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )
    return {
        "msg": "Task deleted",
        "data": deleted_task,
    }


@app.post(
    "/ai/ask",
    response_model=AskResponse,
)
def ai_question(request: AskRequest):
    if not llm_service.api_key or not llm_service.base_url or not llm_service.model:
        raise HTTPException(
            status_code=503,
            detail="模型服务未配置",
        )

    try:
        answer = llm_service.ask_llm(request.question)
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="模型服务暂不可用",
        )

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="模型未返回有效回答",
        )

    return {"answer": answer}