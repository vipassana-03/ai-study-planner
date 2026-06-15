from __future__ import annotations

import json
from pathlib import Path

from models.exception import StudyException


class ExceptionStorage:
    def __init__(self, path: Path = Path("data/exceptions.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[StudyException]:
        return [StudyException.model_validate(item) for item in self._read_raw()]

    def get_by_id(self, exception_id: str) -> StudyException | None:
        for exception in self.get_all():
            if exception.id == exception_id:
                return exception
        return None

    def save_all(self, exceptions: list[StudyException]) -> None:
        self._write_raw([exception.model_dump(mode="json") for exception in exceptions])

    def add(self, exception: StudyException) -> StudyException:
        exceptions = self.get_all()
        exceptions.append(exception)
        self.save_all(exceptions)
        return exception

    def update(self, updated_exception: StudyException) -> StudyException:
        exceptions = self.get_all()
        for index, exception in enumerate(exceptions):
            if exception.id == updated_exception.id:
                exceptions[index] = updated_exception
                self.save_all(exceptions)
                return updated_exception
        raise LookupError("Exception not found")

    def delete(self, exception_id: str) -> None:
        exceptions = self.get_all()
        remaining_exceptions = [
            exception for exception in exceptions if exception.id != exception_id
        ]
        if len(remaining_exceptions) == len(exceptions):
            raise LookupError("Exception not found")
        self.save_all(remaining_exceptions)

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
