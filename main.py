from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    done: bool | None = None


class SearchResponse(BaseModel):
    keyword: str
    skip: int
    limit: int
    data: list[TaskResponse]


class DeletedResponse(BaseModel):
    msg: str
    task: TaskResponse


app = FastAPI(
    title="FastAPI 任务练习",
    description="用于学习路由、参数校验、请求体、响应模型和 CRUD。",
    version="0.1.0",
)


# 暂时使用内存列表模拟数据库；服务重启后会恢复为这些初始数据。
tasks = [
    {"id": 1, "title": "学习 Python", "done": True},
    {"id": 2, "title": "学习 FastAPI", "done": False},
    {"id": 3, "title": "复习 SQL", "done": False},
    {"id": 4, "title": "学习 Git", "done": True},
]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/categories/id/{category_id}")
async def get_category_by_id(
    category_id: int = Path(
        ...,
        ge=1,
        le=100,
        description="新闻分类，ID 范围为 1～100",
    ),
):
    return {"msg": f"新闻 ID 为 {category_id}"}


@app.get("/categories/name/{category_name}")
async def get_category_by_name(
    category_name: str = Path(
        ...,
        min_length=2,
        max_length=10,
    ),
):
    return {"msg": f"分类名称为 {category_name}"}


@app.get(
    "/search",
    response_model=SearchResponse,
)
async def search(
    keyword: Annotated[str, Query(max_length=50)] = "",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    filtered_tasks = []

    for task in tasks:
        if keyword.lower() in task["title"].lower():
            filtered_tasks.append(task)

    selected_tasks = filtered_tasks[skip : skip + limit]

    return {
        "keyword": keyword,
        "skip": skip,
        "limit": limit,
        "data": selected_tasks,
    }


@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
async def get_tasks():
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail="任务不存在",
    )


@app.post(
    "/tasks",
    status_code=201,
    response_model=TaskResponse,
)
async def create_task(task: TaskCreate):
    task_ids = []

    for existing_task in tasks:
        task_ids.append(existing_task["id"])

    new_id = max(task_ids, default=0) + 1
    new_task = {
        "id": new_id,
        **task.model_dump(),
    }

    tasks.append(new_task)
    return new_task


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task(task_id: int, task_update: TaskCreate):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = task_update.title
            task["done"] = task_update.done
            return task

    raise HTTPException(
        status_code=404,
        detail="任务不存在",
    )


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task_partial(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title is not None:
                task["title"] = task_update.title

            if task_update.done is not None:
                task["done"] = task_update.done

            return task

    raise HTTPException(
        status_code=404,
        detail="任务不存在",
    )


@app.delete(
    "/tasks/{task_id}",
    response_model=DeletedResponse,
)
async def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return {
                "msg": "任务删除成功",
                "task": task,
            }

    raise HTTPException(
        status_code=404,
        detail="任务不存在",
    )
