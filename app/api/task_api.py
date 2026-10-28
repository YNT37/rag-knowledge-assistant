from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core import database
from app.schemas.task_schemas import TaskCreate, TaskUpdate, TaskResponse, SearchResponse, DeleteResponse

router = APIRouter()


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
)
async def get_tasks():
    return database.get_all_tasks()


@router.get(
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


def get_data(
        keyword: Annotated[str, Query(max_length=50)] = "",
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    selected_tasks = database.search_tasks(keyword, skip, limit)
    return {
        "keyword": keyword,
        "skip": skip,
        "limit": limit,
        "data": selected_tasks,
    }


@router.get(
    "/search",
    response_model=SearchResponse,
)
async def search_tasks(
        responses: Annotated[dict, Depends(get_data)],
):
    return responses


@router.post(
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


@router.put(
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


@router.patch(
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


@router.delete(
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
