from pydantic import BaseModel, Field


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
