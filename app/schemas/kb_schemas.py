from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.kb_validation import normalize_category_name, normalize_source


PositiveId = Annotated[int, Field(strict=True, gt=0)]


class CategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return normalize_category_name(value)


class DocumentCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    content: Annotated[str, Field(min_length=1, max_length=20000)]
    category_id: PositiveId | None = None

    @field_validator("source")
    @classmethod
    def check_source(cls, value: str) -> str:
        return normalize_source(value)

    @field_validator("content")
    @classmethod
    def check_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("正文不能全为空白")
        return value


class DocumentMoveInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: PositiveId


class CategoryItem(BaseModel):
    id: int
    name: str
    is_default: bool
    document_count: int


class CategoryList(BaseModel):
    count: int
    data: list[CategoryItem]


class CategoryDeleteResult(BaseModel):
    deleted_category_id: int
    moved_count: int
    target_category_id: int


class DocumentItem(BaseModel):
    id: int
    source: str
    category_id: int
    category_name: str


class DocumentList(BaseModel):
    count: int
    data: list[DocumentItem]


class DocumentDetail(DocumentItem):
    content: str
    char_count: int


class DocumentDeleteResult(BaseModel):
    source: str
    deleted: bool
