from __future__ import annotations

import json
from pathlib import Path

from models.availability import CalendarEvent


class CalendarEventStorage:
    def __init__(self, path: Path = Path("data/calendar_events.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[CalendarEvent]:
        return [CalendarEvent.model_validate(item) for item in self._read_raw()]

    def get_by_id(self, event_id: str) -> CalendarEvent | None:
        for event in self.get_all():
            if event.id == event_id:
                return event
        return None

    def save_all(self, events: list[CalendarEvent]) -> None:
        self._write_raw([event.model_dump(mode="json") for event in events])

    def add(self, event: CalendarEvent) -> CalendarEvent:
        events = self.get_all()
        events.append(event)
        self.save_all(events)
        return event

    def update(self, updated_event: CalendarEvent) -> CalendarEvent:
        events = self.get_all()
        for index, event in enumerate(events):
            if event.id == updated_event.id:
                events[index] = updated_event
                self.save_all(events)
                return updated_event
        raise LookupError("Calendar event not found")

    def delete(self, event_id: str) -> None:
        events = self.get_all()
        remaining_events = [event for event in events if event.id != event_id]
        if len(remaining_events) == len(events):
            raise LookupError("Calendar event not found")
        self.save_all(remaining_events)

    def _read_raw(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _write_raw(self, data: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
