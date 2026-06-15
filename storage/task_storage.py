from __future__ import annotations

import json
from pathlib import Path

from models.task import Task


class TaskStorage:
    def __init__(self, path: Path = Path("data/tasks.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[Task]:
        return [Task.model_validate(item) for item in self._read_raw()]

    def get_by_id(self, task_id: str) -> Task | None:
        for task in self.get_all():
            if task.id == task_id:
                return task
        return None

    def save_all(self, tasks: list[Task]) -> None:
        self._write_raw([task.model_dump(mode="json") for task in tasks])

    def add(self, task: Task) -> Task:
        tasks = self.get_all()
        tasks.append(task)
        self.save_all(tasks)
        return task

    def update(self, updated_task: Task) -> Task:
        tasks = self.get_all()
        for index, task in enumerate(tasks):
            if task.id == updated_task.id:
                tasks[index] = updated_task
                self.save_all(tasks)
                return updated_task
        raise LookupError("Task not found")

    def delete(self, task_id: str) -> None:
        tasks = self.get_all()
        remaining_tasks = [task for task in tasks if task.id != task_id]
        if len(remaining_tasks) == len(tasks):
            raise LookupError("Task not found")
        self.save_all(remaining_tasks)

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
