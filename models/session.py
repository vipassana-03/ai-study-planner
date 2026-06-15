from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from models.task import Task


class ScheduledSessionStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    skipped = "skipped"


class CompletionType(str, Enum):
    on_time = "on_time"
    early = "early"
    late = "late"
    skipped = "skipped"


class ScheduledSession(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    task_id: str
    task_name: str
    subject: str
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    planned_hours: float = Field(..., gt=0)
    status: ScheduledSessionStatus = ScheduledSessionStatus.scheduled


class SessionCompletionRequest(BaseModel):
    actual_hours: float | None = Field(default=None, ge=0)


class SessionHistoryEntry(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    session_id: str
    task_id: str
    task_name: str
    subject: str
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    planned_hours: float = Field(..., ge=0)
    actual_hours: float = Field(..., ge=0)
    completion_type: CompletionType
    estimation_error_hours: float
    estimation_accuracy: float = Field(..., ge=0, le=1)
    recorded_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class ScheduleWarning(BaseModel):
    task_id: str
    task_name: str
    due_date: dt.date
    required_hours: float
    scheduled_hours: float
    missing_hours: float
    message: str


class ScheduleGenerationResult(BaseModel):
    schedule: list[ScheduledSession]
    warnings: list[ScheduleWarning] = Field(default_factory=list)


class SessionActionResult(BaseModel):
    history_entry: SessionHistoryEntry
    updated_task: Task
    schedule: list[ScheduledSession]
    warnings: list[ScheduleWarning] = Field(default_factory=list)
