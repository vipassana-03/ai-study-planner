from __future__ import annotations

from uuid import uuid4

from models.session import (
    CompletionType,
    ScheduledSession,
    SessionActionResult,
    SessionCompletionRequest,
    SessionHistoryEntry,
)
from services.rescheduler import ReschedulerService
from storage.schedule_storage import ScheduleStorage
from storage.session_storage import SessionStorage
from storage.task_storage import TaskStorage
from services.task_service import TaskService


class SessionService:
    def __init__(
        self,
        schedule_storage: ScheduleStorage,
        session_storage: SessionStorage,
        task_storage: TaskStorage,
        task_service: TaskService,
        rescheduler_service: ReschedulerService,
    ):
        self.schedule_storage = schedule_storage
        self.session_storage = session_storage
        self.task_storage = task_storage
        self.task_service = task_service
        self.rescheduler_service = rescheduler_service

    def complete_session(
        self,
        session_id: str,
        request: SessionCompletionRequest,
    ) -> SessionActionResult:
        session = self._get_session_or_raise(session_id)
        actual_hours = (
            request.actual_hours
            if request.actual_hours is not None
            else session.planned_hours
        )
        return self._apply_session_result(session, actual_hours, CompletionType.on_time)

    def complete_session_early(
        self,
        session_id: str,
        request: SessionCompletionRequest,
    ) -> SessionActionResult:
        session = self._get_session_or_raise(session_id)
        if request.actual_hours is None:
            raise ValueError("actual_hours is required for early completion")
        if request.actual_hours > session.planned_hours:
            raise ValueError("actual_hours cannot exceed planned_hours for early completion")
        return self._apply_session_result(session, request.actual_hours, CompletionType.early)

    def complete_session_late(
        self,
        session_id: str,
        request: SessionCompletionRequest,
    ) -> SessionActionResult:
        session = self._get_session_or_raise(session_id)
        if request.actual_hours is None:
            raise ValueError("actual_hours is required for late completion")
        if request.actual_hours < session.planned_hours:
            raise ValueError("actual_hours cannot be less than planned_hours for late completion")
        return self._apply_session_result(session, request.actual_hours, CompletionType.late)

    def skip_session(self, session_id: str) -> SessionActionResult:
        session = self._get_session_or_raise(session_id)
        task = self.task_storage.get_by_id(session.task_id)
        if task is None:
            raise LookupError("Task not found for session")

        history_entry = self._create_history_entry(session, 0, CompletionType.skipped)
        self.session_storage.add(history_entry)
        self.schedule_storage.delete(session.id)
        result = self.rescheduler_service.reschedule()

        return SessionActionResult(
            history_entry=history_entry,
            updated_task=task,
            schedule=result.schedule,
            warnings=result.warnings,
        )

    def get_session_history(self) -> list[SessionHistoryEntry]:
        return self.session_storage.get_all()

    def _apply_session_result(
        self,
        session: ScheduledSession,
        actual_hours: float,
        completion_type: CompletionType,
    ) -> SessionActionResult:
        updated_task = self.task_service.record_study_time(session.task_id, actual_hours)
        history_entry = self._create_history_entry(session, actual_hours, completion_type)
        self.session_storage.add(history_entry)
        self.schedule_storage.delete(session.id)
        result = self.rescheduler_service.reschedule()

        return SessionActionResult(
            history_entry=history_entry,
            updated_task=updated_task,
            schedule=result.schedule,
            warnings=result.warnings,
        )

    def _get_session_or_raise(self, session_id: str) -> ScheduledSession:
        session = self.schedule_storage.get_by_id(session_id)
        if session is None:
            raise LookupError("Session not found")
        return session

    def _create_history_entry(
        self,
        session: ScheduledSession,
        actual_hours: float,
        completion_type: CompletionType,
    ) -> SessionHistoryEntry:
        estimation_error = round(actual_hours - session.planned_hours, 2)
        if session.planned_hours == 0:
            estimation_accuracy = 1
        else:
            estimation_accuracy = max(
                0,
                round(1 - abs(estimation_error) / session.planned_hours, 4),
            )

        return SessionHistoryEntry(
            id=str(uuid4()),
            session_id=session.id,
            task_id=session.task_id,
            task_name=session.task_name,
            subject=session.subject,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            planned_hours=session.planned_hours,
            actual_hours=round(actual_hours, 2),
            completion_type=completion_type,
            estimation_error_hours=estimation_error,
            estimation_accuracy=estimation_accuracy,
        )
