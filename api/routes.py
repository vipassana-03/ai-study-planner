from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from models.availability import (
    CalendarEvent,
    CalendarEventCreate,
    CalendarEventUpdate,
    DailyBlock,
    DailyBlockCreate,
    DailyBlockUpdate,
    HolidayCreate,
)
from models.exception import (
    StudyException,
    StudyExceptionCreate,
    StudyExceptionUpdate,
)
from models.session import (
    EstimationAccuracyReport,
    ScheduleGenerationResult,
    ScheduledSession,
    SessionActionResult,
    SessionCompletionRequest,
    SessionHistoryEntry,
)
from models.task import Task, TaskCreate, TaskUpdate
from models.timetable import WeeklyTimetable
from services.availability_service import AvailabilityService
from services.exception_service import ExceptionService
from services.rescheduler import ReschedulerService
from services.scheduler import SchedulerService
from services.session_service import SessionService
from services.task_service import TaskService
from services.timetable_service import TimetableService
from storage.calendar_event_storage import CalendarEventStorage
from storage.daily_block_storage import DailyBlockStorage
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


def get_calendar_event_storage() -> CalendarEventStorage:
    return CalendarEventStorage()


def get_daily_block_storage() -> DailyBlockStorage:
    return DailyBlockStorage()


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


def get_availability_service(
    calendar_event_storage: CalendarEventStorage = Depends(get_calendar_event_storage),
    daily_block_storage: DailyBlockStorage = Depends(get_daily_block_storage),
) -> AvailabilityService:
    return AvailabilityService(calendar_event_storage, daily_block_storage)


def get_scheduler_service(
    task_storage: TaskStorage = Depends(get_task_storage),
    timetable_storage: TimetableStorage = Depends(get_timetable_storage),
    exception_storage: ExceptionStorage = Depends(get_exception_storage),
    schedule_storage: ScheduleStorage = Depends(get_schedule_storage),
    session_storage: SessionStorage = Depends(get_session_storage),
    calendar_event_storage: CalendarEventStorage = Depends(get_calendar_event_storage),
    daily_block_storage: DailyBlockStorage = Depends(get_daily_block_storage),
) -> SchedulerService:
    return SchedulerService(
        task_storage,
        timetable_storage,
        exception_storage,
        schedule_storage,
        session_storage,
        calendar_event_storage,
        daily_block_storage,
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


@router.post(
    "/calendar/events",
    response_model=CalendarEvent,
    status_code=status.HTTP_201_CREATED,
)
def add_calendar_event(
    event_create: CalendarEventCreate,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.add_calendar_event(event_create)
    except Exception as error:
        raise_http_error(error)


@router.post(
    "/calendar/holidays",
    response_model=CalendarEvent,
    status_code=status.HTTP_201_CREATED,
)
def add_holiday(
    holiday_create: HolidayCreate,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.add_holiday(holiday_create)
    except Exception as error:
        raise_http_error(error)


@router.get("/calendar/events", response_model=list[CalendarEvent])
def get_calendar_events(
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    return availability_service.get_calendar_events()


@router.get("/calendar/events/{event_id}", response_model=CalendarEvent)
def get_calendar_event_by_id(
    event_id: str,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.get_calendar_event_by_id(event_id)
    except Exception as error:
        raise_http_error(error)


@router.put("/calendar/events/{event_id}", response_model=CalendarEvent)
def update_calendar_event(
    event_id: str,
    event_update: CalendarEventUpdate,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.update_calendar_event(event_id, event_update)
    except Exception as error:
        raise_http_error(error)


@router.delete("/calendar/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(
    event_id: str,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        availability_service.delete_calendar_event(event_id)
    except Exception as error:
        raise_http_error(error)


@router.post(
    "/daily-blocks",
    response_model=DailyBlock,
    status_code=status.HTTP_201_CREATED,
)
def add_daily_block(
    block_create: DailyBlockCreate,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.add_daily_block(block_create)
    except Exception as error:
        raise_http_error(error)


@router.get("/daily-blocks", response_model=list[DailyBlock])
def get_daily_blocks(
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    return availability_service.get_daily_blocks()


@router.get("/daily-blocks/{block_id}", response_model=DailyBlock)
def get_daily_block_by_id(
    block_id: str,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.get_daily_block_by_id(block_id)
    except Exception as error:
        raise_http_error(error)


@router.put("/daily-blocks/{block_id}", response_model=DailyBlock)
def update_daily_block(
    block_id: str,
    block_update: DailyBlockUpdate,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        return availability_service.update_daily_block(block_id, block_update)
    except Exception as error:
        raise_http_error(error)


@router.delete("/daily-blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_block(
    block_id: str,
    availability_service: AvailabilityService = Depends(get_availability_service),
):
    try:
        availability_service.delete_daily_block(block_id)
    except Exception as error:
        raise_http_error(error)


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


@router.get("/sessions/accuracy", response_model=EstimationAccuracyReport)
def get_estimation_accuracy(
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.get_estimation_accuracy()
