from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import uuid4

from models.availability import BlockType, CalendarEvent, DailyBlock
from models.session import (
    ScheduleGenerationResult,
    ScheduledSession,
    ScheduleSlotType,
    ScheduleWarning,
)
from models.task import Task
from models.timetable import TimeSlot, WeeklyTimetable
from storage.calendar_event_storage import CalendarEventStorage
from storage.daily_block_storage import DailyBlockStorage
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
        calendar_event_storage: CalendarEventStorage,
        daily_block_storage: DailyBlockStorage,
    ):
        self.task_storage = task_storage
        self.timetable_storage = timetable_storage
        self.exception_storage = exception_storage
        self.schedule_storage = schedule_storage
        self.session_storage = session_storage
        self.calendar_event_storage = calendar_event_storage
        self.daily_block_storage = daily_block_storage

    def generate_schedule(self) -> ScheduleGenerationResult:
        tasks = self._get_schedulable_tasks()
        if not tasks:
            self.schedule_storage.save_all([])
            return ScheduleGenerationResult(schedule=[], warnings=[])

        today = date.today()
        max_due_date = max(task.due_date for task in tasks)
        timetable = self.timetable_storage.get()
        slot_pools = self._build_slot_pools(timetable, today, max_due_date)

        schedule: list[ScheduledSession] = []
        warnings: list[ScheduleWarning] = []

        for task in tasks:
            remaining_minutes = self._remaining_minutes(task)
            required_minutes = remaining_minutes
            scheduled_minutes = 0

            for slot_type in (ScheduleSlotType.free, ScheduleSlotType.flexible):
                if remaining_minutes <= 0:
                    break

                for slot in slot_pools[slot_type.value]:
                    if remaining_minutes <= 0:
                        break
                    if slot["date"] > task.due_date:
                        continue

                    slot_minutes = self._minutes_between(
                        slot["start_time"],
                        slot["end_time"],
                    )
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
                            slot_type=slot_type,
                            sacrificed_items=slot["sacrificed_items"],
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
                            f"Insufficient available free and flexible time before "
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

    def _build_slot_pools(
        self,
        timetable: WeeklyTimetable,
        start_date: date,
        end_date: date,
    ) -> dict[str, list[dict]]:
        exceptions = self.exception_storage.get_all()
        calendar_events = self.calendar_event_storage.get_all()
        daily_blocks = self.daily_block_storage.get_all()
        history_entries = self.session_storage.get_all()
        free_slots: list[dict] = []
        flexible_slots: list[dict] = []
        current_date = start_date

        while current_date <= end_date:
            weekday_name = current_date.strftime("%A").lower()
            weekly_slots: list[TimeSlot] = getattr(timetable, weekday_name)
            protected_intervals: list[dict] = []
            flexible_intervals: list[dict] = []

            for exception in exceptions:
                if exception.date != current_date:
                    continue
                interval = {
                    "start": exception.start_time,
                    "end": exception.end_time,
                    "names": [f"Exception: {exception.reason}"],
                }
                if exception.block_type == BlockType.flexible:
                    flexible_intervals.append(interval)
                else:
                    protected_intervals.append(interval)

            for event in calendar_events:
                if not self._event_applies_on_date(event, current_date):
                    continue
                interval = self._interval_for_event(event)
                if event.block_type == BlockType.flexible:
                    flexible_intervals.append(interval)
                else:
                    protected_intervals.append(interval)

            for block in daily_blocks:
                if not self._block_applies_on_date(block, weekday_name):
                    continue
                interval = {
                    "start": block.start_time,
                    "end": block.end_time,
                    "names": [f"Daily block: {block.name}"],
                }
                if block.block_type == BlockType.flexible:
                    flexible_intervals.append(interval)
                else:
                    protected_intervals.append(interval)

            for entry in history_entries:
                if entry.date != current_date or entry.actual_hours <= 0:
                    continue
                protected_intervals.append(
                    {
                        "start": entry.start_time,
                        "end": entry.end_time,
                        "names": [f"Completed session: {entry.task_name}"],
                    }
                )

            protected_intervals = self._merge_named_intervals(protected_intervals)
            flexible_intervals = self._merge_named_intervals(flexible_intervals)

            protected_pairs = [
                (interval["start"], interval["end"]) for interval in protected_intervals
            ]
            flexible_pairs = [
                (interval["start"], interval["end"]) for interval in flexible_intervals
            ]

            for weekly_slot in weekly_slots:
                available_segments = self._subtract_blocked_intervals(
                    weekly_slot.start_time,
                    weekly_slot.end_time,
                    protected_pairs,
                )

                for segment_start, segment_end in available_segments:
                    for free_start, free_end in self._subtract_blocked_intervals(
                        segment_start,
                        segment_end,
                        flexible_pairs,
                    ):
                        free_slots.append(
                            {
                                "date": current_date,
                                "start_time": free_start,
                                "end_time": free_end,
                                "sacrificed_items": [],
                            }
                        )

                for flexible_interval in flexible_intervals:
                    intersection = self._intersect_interval(
                        weekly_slot.start_time,
                        weekly_slot.end_time,
                        flexible_interval["start"],
                        flexible_interval["end"],
                    )
                    if intersection is None:
                        continue

                    for flex_start, flex_end in self._subtract_blocked_intervals(
                        intersection[0],
                        intersection[1],
                        protected_pairs,
                    ):
                        flexible_slots.append(
                            {
                                "date": current_date,
                                "start_time": flex_start,
                                "end_time": flex_end,
                                "sacrificed_items": flexible_interval["names"],
                            }
                        )

            current_date += timedelta(days=1)

        return {
            "free": self._sort_slots(free_slots),
            "flexible": self._sort_slots(flexible_slots),
        }

    def _event_applies_on_date(self, event: CalendarEvent, target_date: date) -> bool:
        if event.recurring_yearly:
            return event.date.month == target_date.month and event.date.day == target_date.day
        return event.date == target_date

    def _block_applies_on_date(self, block: DailyBlock, weekday_name: str) -> bool:
        return block.enabled and weekday_name in block.active_days

    def _interval_for_event(self, event: CalendarEvent) -> dict:
        if event.is_full_day:
            start_time = time.min
            end_time = time.max
        else:
            start_time = event.start_time
            end_time = event.end_time

        return {
            "start": start_time,
            "end": end_time,
            "names": [f"{event.event_type}: {event.name}"],
        }

    def _merge_named_intervals(self, intervals: list[dict]) -> list[dict]:
        if not intervals:
            return []

        ordered = sorted(intervals, key=lambda item: (item["start"], item["end"]))
        merged = [
            {
                "start": ordered[0]["start"],
                "end": ordered[0]["end"],
                "names": list(ordered[0]["names"]),
            }
        ]

        for interval in ordered[1:]:
            current = merged[-1]
            if interval["start"] <= current["end"]:
                current["end"] = max(current["end"], interval["end"])
                current["names"] = self._unique_names(
                    current["names"] + interval["names"]
                )
            else:
                merged.append(
                    {
                        "start": interval["start"],
                        "end": interval["end"],
                        "names": list(interval["names"]),
                    }
                )

        return merged

    def _unique_names(self, names: list[str]) -> list[str]:
        unique_names = []
        for name in names:
            if name not in unique_names:
                unique_names.append(name)
        return unique_names

    def _sort_slots(self, slots: list[dict]) -> list[dict]:
        return sorted(slots, key=lambda slot: (slot["date"], slot["start_time"]))

    def _intersect_interval(
        self,
        first_start: time,
        first_end: time,
        second_start: time,
        second_end: time,
    ) -> tuple[time, time] | None:
        start_time = max(first_start, second_start)
        end_time = min(first_end, second_end)
        if end_time <= start_time:
            return None
        return start_time, end_time

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
