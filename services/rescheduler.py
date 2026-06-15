from __future__ import annotations

from models.session import ScheduleGenerationResult
from services.scheduler import SchedulerService


class ReschedulerService:
    def __init__(self, scheduler_service: SchedulerService):
        self.scheduler_service = scheduler_service

    def reschedule(self) -> ScheduleGenerationResult:
        return self.scheduler_service.generate_schedule()
