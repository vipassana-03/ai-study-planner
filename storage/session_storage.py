from __future__ import annotations

import json
from pathlib import Path

from models.session import SessionHistoryEntry


class SessionStorage:
    def __init__(self, path: Path = Path("data/session_history.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[SessionHistoryEntry]:
        return [SessionHistoryEntry.model_validate(item) for item in self._read_raw()]

    def add(self, entry: SessionHistoryEntry) -> SessionHistoryEntry:
        entries = self.get_all()
        entries.append(entry)
        self.save_all(entries)
        return entry

    def save_all(self, entries: list[SessionHistoryEntry]) -> None:
        self._write_raw([entry.model_dump(mode="json") for entry in entries])

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
