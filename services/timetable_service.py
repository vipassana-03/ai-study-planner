from __future__ import annotations

from models.timetable import WeeklyTimetable
from storage.timetable_storage import TimetableStorage


class TimetableService:
    def __init__(self, timetable_storage: TimetableStorage):
        self.timetable_storage = timetable_storage

    def create_weekly_timetable(self, timetable: WeeklyTimetable) -> WeeklyTimetable:
        return self.timetable_storage.save(timetable)

    def update_weekly_timetable(self, timetable: WeeklyTimetable) -> WeeklyTimetable:
        return self.timetable_storage.save(timetable)

    def get_weekly_timetable(self) -> WeeklyTimetable:
        return self.timetable_storage.get()
