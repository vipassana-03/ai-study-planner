from __future__ import annotations

from datetime import time
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class TimeSlot(BaseModel):
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class WeeklyTimetable(BaseModel):
    monday: list[TimeSlot] = Field(default_factory=list)
    tuesday: list[TimeSlot] = Field(default_factory=list)
    wednesday: list[TimeSlot] = Field(default_factory=list)
    thursday: list[TimeSlot] = Field(default_factory=list)
    friday: list[TimeSlot] = Field(default_factory=list)
    saturday: list[TimeSlot] = Field(default_factory=list)
    sunday: list[TimeSlot] = Field(default_factory=list)
