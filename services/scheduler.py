from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import uuid4

from models.session import (
    ScheduleGenerationResult,
    ScheduledSession,
    ScheduleWarning,
)
from models.task import Task
from models.timetable import TimeSlot, WeeklyTimetable
from storage.exception_storage import ExceptionStorage
from storage.schedule_storage import ScheduleStorage
from storage.session_storage import SessionStorage
from storage.task_storage import TaskStorage
from storage.timetable_storage import TimetableStorage


class SchedulerService:
    def __init__(
        self,
        task_storage: TaskStorage,
        timetable_storage: TimetableStorage,
        exception_storage: ExceptionStorage,
        schedule_storage: ScheduleStorage,
        session_storage: SessionStorage,
    ):
        self.task_storage = task_storage
        self.timetable_storage = timetable_storage
        self.exception_storage = exception_storage
        self.schedule_storage = schedule_storage
        self.session_storage = session_storage

    def generate_schedule(self) -> ScheduleGenerationResult:
        tasks = self._get_schedulable_tasks()
        if not tasks:
            self.schedule_storage.save_all([])
            return ScheduleGenerationResult(schedule=[], warnings=[])

        today = date.today()
        max_due_date = max(task.due_date for task in tasks)
        timetable = self.timetable_storage.get()
        available_slots = self._build_available_slots(timetable, today, max_due_date)

        schedule: list[ScheduledSession] = []
        warnings: list[ScheduleWarning] = []

        for task in tasks:
            remaining_minutes = self._remaining_minutes(task)
            required_minutes = remaining_minutes
            scheduled_minutes = 0

            for slot in available_slots:
                if remaining_minutes <= 0:
                    break
                if slot["date"] > task.due_date:
                    continue

                slot_minutes = self._minutes_between(slot["start_time"], slot["end_time"])
                if slot_minutes <= 0:
                    continue

                minutes_to_schedule = min(slot_minutes, remaining_minutes)
                session_start = slot["start_time"]
                session_end = self._add_minutes(session_start, minutes_to_schedule)

                schedule.append(
                    ScheduledSession(
                        id=str(uuid4()),
                        task_id=task.id,
                        task_name=task.name,
                        subject=task.subject,
                        date=slot["date"],
                        start_time=session_start,
                        end_time=session_end,
                        planned_hours=round(minutes_to_schedule / 60, 2),
                    )
                )

                slot["start_time"] = session_end
                remaining_minutes -= minutes_to_schedule
                scheduled_minutes += minutes_to_schedule

            if remaining_minutes > 0:
                missing_hours = round(remaining_minutes / 60, 2)
                warnings.append(
                    ScheduleWarning(
                        task_id=task.id,
                        task_name=task.name,
                        due_date=task.due_date,
                        required_hours=round(required_minutes / 60, 2),
                        scheduled_hours=round(scheduled_minutes / 60, 2),
                        missing_hours=missing_hours,
                        message=(
                            f"Insufficient available time before "
                            f"{task.due_date.isoformat()} for {task.name}. "
                            f"Missing {missing_hours} hour(s)."
                        ),
                    )
                )

        self.schedule_storage.save_all(schedule)
        return ScheduleGenerationResult(schedule=schedule, warnings=warnings)

    def get_schedule(self) -> list[ScheduledSession]:
        return self.schedule_storage.get_all()

    def _get_schedulable_tasks(self) -> list[Task]:
        tasks = []
        for task in self.task_storage.get_all():
            if task.due_date < date.today():
                continue
            if self._remaining_minutes(task) > 0:
                tasks.append(task)
        return sorted(tasks, key=lambda task: (task.due_date, task.created_at))

    def _remaining_minutes(self, task: Task) -> int:
        remaining_hours = max(task.hours_needed - task.hours_completed, 0)
        return int(round(remaining_hours * 60))

    def _build_available_slots(
        self,
        timetable: WeeklyTimetable,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        exceptions = self.exception_storage.get_all()
        history_entries = self.session_storage.get_all()
        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            weekday_name = current_date.strftime("%A").lower()
            weekly_slots: list[TimeSlot] = getattr(timetable, weekday_name)
            blocked_intervals = [
                (exception.start_time, exception.end_time)
                for exception in exceptions
                if exception.date == current_date
            ]
            blocked_intervals.extend(
                (entry.start_time, entry.end_time)
                for entry in history_entries
                if entry.date == current_date
            )

            for weekly_slot in weekly_slots:
                for start_time, end_time in self._subtract_blocked_intervals(
                    weekly_slot.start_time,
                    weekly_slot.end_time,
                    blocked_intervals,
                ):
                    available_slots.append(
                        {
                            "date": current_date,
                            "start_time": start_time,
                            "end_time": end_time,
                        }
                    )

            current_date += timedelta(days=1)

        return sorted(
            available_slots,
            key=lambda slot: (slot["date"], slot["start_time"]),
        )

    def _subtract_blocked_intervals(
        self,
        slot_start: time,
        slot_end: time,
        blocked_intervals: list[tuple[time, time]],
    ) -> list[tuple[time, time]]:
        segments = [(slot_start, slot_end)]

        for blocked_start, blocked_end in sorted(blocked_intervals):
            next_segments = []
            for segment_start, segment_end in segments:
                if blocked_end <= segment_start or blocked_start >= segment_end:
                    next_segments.append((segment_start, segment_end))
                    continue

                if blocked_start > segment_start:
                    next_segments.append((segment_start, min(blocked_start, segment_end)))
                if blocked_end < segment_end:
                    next_segments.append((max(blocked_end, segment_start), segment_end))

            segments = next_segments

        return [
            (segment_start, segment_end)
            for segment_start, segment_end in segments
            if segment_end > segment_start
        ]

    def _minutes_between(self, start_time: time, end_time: time) -> int:
        start_datetime = datetime.combine(date.today(), start_time)
        end_datetime = datetime.combine(date.today(), end_time)
        return int((end_datetime - start_datetime).total_seconds() // 60)

    def _add_minutes(self, start_time: time, minutes: int) -> time:
        start_datetime = datetime.combine(date.today(), start_time)
        end_datetime = start_datetime + timedelta(minutes=minutes)
        return end_datetime.time().replace(second=0, microsecond=0)
