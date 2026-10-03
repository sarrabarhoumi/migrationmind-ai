from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    source_file: str | None
    output_file: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TargetField(BaseModel):
    name: str
    label: str | None = None
    type: Literal["string", "integer", "float", "date", "datetime", "email", "phone", "boolean"] = "string"
    required: bool = False
    unique: bool = False
    aliases: list[str] = []
    default: Any | None = None


class TargetSchema(BaseModel):
    entity: str
    description: str | None = None
    fields: list[TargetField]


class MappingItem(BaseModel):
    target_field: str
    source_field: str | None = None
    transformation: str = "direct"
    confidence: float = Field(ge=0, le=1)
    explanation: str = ""
    approved: bool = False


class MappingUpdate(BaseModel):
    mappings: list[MappingItem]


class DryRunRequest(BaseModel):
    row_limit: int = Field(default=5000, ge=1, le=100000)


class ExecuteRequest(BaseModel):
    approved_by: str = Field(default="Portfolio User", min_length=2, max_length=120)
