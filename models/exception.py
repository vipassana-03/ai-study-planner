from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, model_validator

from models.availability import BlockType


class StudyExceptionBase(BaseModel):
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    reason: str = Field(default="Unavailable", min_length=1)
    block_type: BlockType = BlockType.protected

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class StudyExceptionCreate(StudyExceptionBase):
    pass


class StudyExceptionUpdate(BaseModel):
    date: dt.date | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    reason: str | None = Field(default=None, min_length=1)
    block_type: BlockType | None = None

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class StudyException(StudyExceptionBase):
    id: str
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
