from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from models.exception import (
    StudyException,
    StudyExceptionCreate,
    StudyExceptionUpdate,
)
from models.session import (
    ScheduleGenerationResult,
    ScheduledSession,
    SessionActionResult,
    SessionCompletionRequest,
    SessionHistoryEntry,
)
from models.task import Task, TaskCreate, TaskUpdate
from models.timetable import WeeklyTimetable
from services.exception_service import ExceptionService
from services.rescheduler import ReschedulerService
from services.scheduler import SchedulerService
from services.session_service import SessionService
from services.task_service import TaskService
from services.timetable_service import TimetableService
from storage.exception_storage import ExceptionStorage
from storage.schedule_storage import ScheduleStorage
from storage.session_storage import SessionStorage
from storage.task_storage import TaskStorage
from storage.timetable_storage import TimetableStorage


router = APIRouter(prefix="/api/v1")


def get_task_storage() -> TaskStorage:
    return TaskStorage()


def get_timetable_storage() -> TimetableStorage:
    return TimetableStorage()


def get_exception_storage() -> ExceptionStorage:
    return ExceptionStorage()


def get_schedule_storage() -> ScheduleStorage:
    return ScheduleStorage()


def get_session_storage() -> SessionStorage:
    return SessionStorage()


def get_task_service(
    task_storage: TaskStorage = Depends(get_task_storage),
) -> TaskService:
    return TaskService(task_storage)


def get_timetable_service(
    timetable_storage: TimetableStorage = Depends(get_timetable_storage),
) -> TimetableService:
    return TimetableService(timetable_storage)


def get_exception_service(
    exception_storage: ExceptionStorage = Depends(get_exception_storage),
) -> ExceptionService:
    return ExceptionService(exception_storage)


def get_scheduler_service(
    task_storage: TaskStorage = Depends(get_task_storage),
    timetable_storage: TimetableStorage = Depends(get_timetable_storage),
    exception_storage: ExceptionStorage = Depends(get_exception_storage),
    schedule_storage: ScheduleStorage = Depends(get_schedule_storage),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> SchedulerService:
    return SchedulerService(
        task_storage,
        timetable_storage,
        exception_storage,
        schedule_storage,
        session_storage,
    )


def get_rescheduler_service(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ReschedulerService:
    return ReschedulerService(scheduler_service)


def get_session_service(
    schedule_storage: ScheduleStorage = Depends(get_schedule_storage),
    session_storage: SessionStorage = Depends(get_session_storage),
    task_storage: TaskStorage = Depends(get_task_storage),
    task_service: TaskService = Depends(get_task_service),
    rescheduler_service: ReschedulerService = Depends(get_rescheduler_service),
) -> SessionService:
    return SessionService(
        schedule_storage,
        session_storage,
        task_storage,
        task_service,
        rescheduler_service,
    )


def raise_http_error(error: Exception) -> None:
    if isinstance(error, LookupError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error)) from error
    raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(
    task_create: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return task_service.create_task(task_create)
    except Exception as error:
        raise_http_error(error)


@router.get("/tasks", response_model=list[Task])
def get_all_tasks(task_service: TaskService = Depends(get_task_service)):
    return task_service.get_all_tasks()


@router.get("/tasks/{task_id}", response_model=Task)
def get_task_by_id(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return task_service.get_task_by_id(task_id)
    except Exception as error:
        raise_http_error(error)


@router.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: str,
    task_update: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return task_service.update_task(task_id, task_update)
    except Exception as error:
        raise_http_error(error)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        task_service.delete_task(task_id)
    except Exception as error:
        raise_http_error(error)


@router.post("/timetable", response_model=WeeklyTimetable, status_code=status.HTTP_201_CREATED)
def create_weekly_timetable(
    timetable: WeeklyTimetable,
    timetable_service: TimetableService = Depends(get_timetable_service),
):
    return timetable_service.create_weekly_timetable(timetable)


@router.put("/timetable", response_model=WeeklyTimetable)
def update_weekly_timetable(
    timetable: WeeklyTimetable,
    timetable_service: TimetableService = Depends(get_timetable_service),
):
    return timetable_service.update_weekly_timetable(timetable)


@router.get("/timetable", response_model=WeeklyTimetable)
def get_weekly_timetable(
    timetable_service: TimetableService = Depends(get_timetable_service),
):
    return timetable_service.get_weekly_timetable()


@router.post(
    "/exceptions",
    response_model=StudyException,
    status_code=status.HTTP_201_CREATED,
)
def add_exception(
    exception_create: StudyExceptionCreate,
    exception_service: ExceptionService = Depends(get_exception_service),
):
    try:
        return exception_service.add_exception(exception_create)
    except Exception as error:
        raise_http_error(error)


@router.put("/exceptions/{exception_id}", response_model=StudyException)
def update_exception(
    exception_id: str,
    exception_update: StudyExceptionUpdate,
    exception_service: ExceptionService = Depends(get_exception_service),
):
    try:
        return exception_service.update_exception(exception_id, exception_update)
    except Exception as error:
        raise_http_error(error)


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(
    exception_id: str,
    exception_service: ExceptionService = Depends(get_exception_service),
):
    try:
        exception_service.delete_exception(exception_id)
    except Exception as error:
        raise_http_error(error)


@router.get("/exceptions", response_model=list[StudyException])
def get_exceptions(
    exception_service: ExceptionService = Depends(get_exception_service),
):
    return exception_service.get_exceptions()


@router.post("/schedule/generate", response_model=ScheduleGenerationResult)
def generate_schedule(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
):
    return scheduler_service.generate_schedule()


@router.get("/schedule", response_model=list[ScheduledSession])
def view_schedule(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
):
    return scheduler_service.get_schedule()


@router.post("/sessions/{session_id}/complete", response_model=SessionActionResult)
def complete_session(
    session_id: str,
    request: SessionCompletionRequest | None = None,
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.complete_session(
            session_id,
            request or SessionCompletionRequest(),
        )
    except Exception as error:
        raise_http_error(error)


@router.post("/sessions/{session_id}/complete-early", response_model=SessionActionResult)
def complete_session_early(
    session_id: str,
    request: SessionCompletionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.complete_session_early(session_id, request)
    except Exception as error:
        raise_http_error(error)


@router.post("/sessions/{session_id}/complete-late", response_model=SessionActionResult)
def complete_session_late(
    session_id: str,
    request: SessionCompletionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.complete_session_late(session_id, request)
    except Exception as error:
        raise_http_error(error)


@router.post("/sessions/{session_id}/skip", response_model=SessionActionResult)
def skip_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.skip_session(session_id)
    except Exception as error:
        raise_http_error(error)


@router.get("/sessions/history", response_model=list[SessionHistoryEntry])
def get_session_history(
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.get_session_history()
