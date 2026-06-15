from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.exception import (
    StudyException,
    StudyExceptionCreate,
    StudyExceptionUpdate,
)
from storage.exception_storage import ExceptionStorage


class ExceptionService:
    def __init__(self, exception_storage: ExceptionStorage):
        self.exception_storage = exception_storage

    def add_exception(self, exception_create: StudyExceptionCreate) -> StudyException:
        exception = StudyException(
            id=str(uuid4()),
            date=exception_create.date,
            start_time=exception_create.start_time,
            end_time=exception_create.end_time,
            reason=exception_create.reason,
        )
        return self.exception_storage.add(exception)

    def update_exception(
        self,
        exception_id: str,
        exception_update: StudyExceptionUpdate,
    ) -> StudyException:
        exception = self.exception_storage.get_by_id(exception_id)
        if exception is None:
            raise LookupError("Exception not found")

        data = exception.model_dump()
        data.update(exception_update.model_dump(exclude_unset=True))
        data["updated_at"] = datetime.utcnow()
        updated_exception = StudyException.model_validate(data)
        return self.exception_storage.update(updated_exception)

    def delete_exception(self, exception_id: str) -> None:
        self.exception_storage.delete(exception_id)

    def get_exceptions(self) -> list[StudyException]:
        return self.exception_storage.get_all()
