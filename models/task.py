from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1)
    subject: str = Field(default="General", min_length=1)
    due_date: date
    hours_needed: float = Field(..., gt=0)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    due_date: date | None = None
    hours_needed: float | None = Field(default=None, gt=0)
    hours_completed: float | None = Field(default=None, ge=0)
    status: TaskStatus | None = None


class Task(TaskBase):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    hours_completed: float = Field(default=0, ge=0)
    status: TaskStatus = TaskStatus.pending
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
