from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.timetable import Weekday


class BlockType(str, Enum):
    protected = "protected"
    flexible = "flexible"


class CalendarEventType(str, Enum):
    holiday = "holiday"
    one_time_exception = "one_time_exception"
    birthday = "birthday"
    special_event = "special_event"


class DailyBlockCategory(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    bath = "bath"
    travel = "travel"
    custom = "custom"


class CalendarEventBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1)
    date: dt.date
    event_type: CalendarEventType = CalendarEventType.one_time_exception
    block_type: BlockType = BlockType.protected
    is_full_day: bool = False
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    recurring_yearly: bool = False

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.is_full_day:
            return self
        if self.start_time is None or self.end_time is None:
            raise ValueError("start_time and end_time are required unless is_full_day is true")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class CalendarEventCreate(CalendarEventBase):
    pass


class HolidayCreate(BaseModel):
    name: str = Field(..., min_length=1)
    date: dt.date
    recurring_yearly: bool = False


class CalendarEventUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(default=None, min_length=1)
    date: dt.date | None = None
    event_type: CalendarEventType | None = None
    block_type: BlockType | None = None
    is_full_day: bool | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    recurring_yearly: bool | None = None


class CalendarEvent(CalendarEventBase):
    id: str
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class DailyBlockBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1)
    category: DailyBlockCategory = DailyBlockCategory.custom
    start_time: dt.time
    end_time: dt.time
    block_type: BlockType = BlockType.protected
    active_days: list[Weekday] = Field(default_factory=lambda: list(Weekday))
    enabled: bool = True

    @model_validator(mode="after")
    def validate_daily_block(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if not self.active_days:
            raise ValueError("active_days cannot be empty")
        return self


class DailyBlockCreate(DailyBlockBase):
    pass


class DailyBlockUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(default=None, min_length=1)
    category: DailyBlockCategory | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    block_type: BlockType | None = None
    active_days: list[Weekday] | None = None
    enabled: bool | None = None


class DailyBlock(DailyBlockBase):
    id: str
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
