from __future__ import annotations

import json
from pathlib import Path

from models.session import ScheduledSession


class ScheduleStorage:
    def __init__(self, path: Path = Path("data/schedule.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[ScheduledSession]:
        return [ScheduledSession.model_validate(item) for item in self._read_raw()]

    def get_by_id(self, session_id: str) -> ScheduledSession | None:
        for session in self.get_all():
            if session.id == session_id:
                return session
        return None

    def save_all(self, sessions: list[ScheduledSession]) -> None:
        self._write_raw([session.model_dump(mode="json") for session in sessions])

    def delete(self, session_id: str) -> None:
        sessions = self.get_all()
        remaining_sessions = [session for session in sessions if session.id != session_id]
        self.save_all(remaining_sessions)

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
