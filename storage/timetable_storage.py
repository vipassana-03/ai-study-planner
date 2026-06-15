from __future__ import annotations

import json
from pathlib import Path

from models.timetable import WeeklyTimetable


class TimetableStorage:
    def __init__(self, path: Path = Path("data/timetable.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(WeeklyTimetable())

    def get(self) -> WeeklyTimetable:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return WeeklyTimetable.model_validate(data if isinstance(data, dict) else {})
        except json.JSONDecodeError:
            return WeeklyTimetable()

    def save(self, timetable: WeeklyTimetable) -> WeeklyTimetable:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(timetable.model_dump(mode="json"), file, indent=4)
        return timetable
