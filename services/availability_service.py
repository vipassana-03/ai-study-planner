from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.availability import (
    BlockType,
    CalendarEvent,
    CalendarEventCreate,
    CalendarEventType,
    CalendarEventUpdate,
    DailyBlock,
    DailyBlockCreate,
    DailyBlockUpdate,
    HolidayCreate,
)
from storage.calendar_event_storage import CalendarEventStorage
from storage.daily_block_storage import DailyBlockStorage


class AvailabilityService:
    def __init__(
        self,
        calendar_event_storage: CalendarEventStorage,
        daily_block_storage: DailyBlockStorage,
    ):
        self.calendar_event_storage = calendar_event_storage
        self.daily_block_storage = daily_block_storage

    def add_calendar_event(self, event_create: CalendarEventCreate) -> CalendarEvent:
        event = CalendarEvent(
            id=str(uuid4()),
            name=event_create.name,
            date=event_create.date,
            event_type=event_create.event_type,
            block_type=event_create.block_type,
            is_full_day=event_create.is_full_day,
            start_time=event_create.start_time,
            end_time=event_create.end_time,
            recurring_yearly=event_create.recurring_yearly,
        )
        return self.calendar_event_storage.add(event)

    def add_holiday(self, holiday_create: HolidayCreate) -> CalendarEvent:
        return self.add_calendar_event(
            CalendarEventCreate(
                name=holiday_create.name,
                date=holiday_create.date,
                event_type=CalendarEventType.holiday,
                block_type=BlockType.protected,
                is_full_day=True,
                recurring_yearly=holiday_create.recurring_yearly,
            )
        )

    def get_calendar_events(self) -> list[CalendarEvent]:
        return self.calendar_event_storage.get_all()

    def get_calendar_event_by_id(self, event_id: str) -> CalendarEvent:
        event = self.calendar_event_storage.get_by_id(event_id)
        if event is None:
            raise LookupError("Calendar event not found")
        return event

    def update_calendar_event(
        self,
        event_id: str,
        event_update: CalendarEventUpdate,
    ) -> CalendarEvent:
        event = self.get_calendar_event_by_id(event_id)
        data = event.model_dump()
        data.update(event_update.model_dump(exclude_unset=True))
        data["updated_at"] = datetime.utcnow()
        updated_event = CalendarEvent.model_validate(data)
        return self.calendar_event_storage.update(updated_event)

    def delete_calendar_event(self, event_id: str) -> None:
        self.calendar_event_storage.delete(event_id)

    def add_daily_block(self, block_create: DailyBlockCreate) -> DailyBlock:
        block = DailyBlock(
            id=str(uuid4()),
            name=block_create.name,
            category=block_create.category,
            start_time=block_create.start_time,
            end_time=block_create.end_time,
            block_type=block_create.block_type,
            active_days=block_create.active_days,
            enabled=block_create.enabled,
        )
        return self.daily_block_storage.add(block)

    def get_daily_blocks(self) -> list[DailyBlock]:
        return self.daily_block_storage.get_all()

    def get_daily_block_by_id(self, block_id: str) -> DailyBlock:
        block = self.daily_block_storage.get_by_id(block_id)
        if block is None:
            raise LookupError("Daily block not found")
        return block

    def update_daily_block(
        self,
        block_id: str,
        block_update: DailyBlockUpdate,
    ) -> DailyBlock:
        block = self.get_daily_block_by_id(block_id)
        data = block.model_dump()
        data.update(block_update.model_dump(exclude_unset=True))
        data["updated_at"] = datetime.utcnow()
        updated_block = DailyBlock.model_validate(data)
        return self.daily_block_storage.update(updated_block)

    def delete_daily_block(self, block_id: str) -> None:
        self.daily_block_storage.delete(block_id)
