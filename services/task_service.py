from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.task import Task, TaskCreate, TaskStatus, TaskUpdate
from storage.task_storage import TaskStorage


class TaskService:
    def __init__(self, task_storage: TaskStorage):
        self.task_storage = task_storage

    def create_task(self, task_create: TaskCreate) -> Task:
        task = Task(
            id=str(uuid4()),
            name=task_create.name,
            subject=task_create.subject,
            due_date=task_create.due_date,
            hours_needed=task_create.hours_needed,
            hours_completed=0,
            status=TaskStatus.pending,
        )
        return self.task_storage.add(task)

    def get_all_tasks(self) -> list[Task]:
        return self.task_storage.get_all()

    def get_task_by_id(self, task_id: str) -> Task:
        task = self.task_storage.get_by_id(task_id)
        if task is None:
            raise LookupError("Task not found")
        return task

    def update_task(self, task_id: str, task_update: TaskUpdate) -> Task:
        task = self.get_task_by_id(task_id)
        data = task.model_dump()
        update_data = task_update.model_dump(exclude_unset=True)
        data.update(update_data)
        data["hours_completed"] = min(data["hours_completed"], data["hours_needed"])
        data["status"] = self._status_for_hours(
            data["hours_completed"],
            data["hours_needed"],
        )
        data["updated_at"] = datetime.utcnow()
        updated_task = Task.model_validate(data)
        return self.task_storage.update(updated_task)

    def delete_task(self, task_id: str) -> None:
        self.task_storage.delete(task_id)

    def record_study_time(self, task_id: str, actual_hours: float) -> Task:
        if actual_hours < 0:
            raise ValueError("actual_hours cannot be negative")

        task = self.get_task_by_id(task_id)
        completed_hours = min(task.hours_completed + actual_hours, task.hours_needed)
        data = task.model_dump()
        data["hours_completed"] = round(completed_hours, 2)
        data["status"] = self._status_for_hours(completed_hours, task.hours_needed)
        data["updated_at"] = datetime.utcnow()
        updated_task = Task.model_validate(data)
        return self.task_storage.update(updated_task)

    def _status_for_hours(self, completed_hours: float, needed_hours: float) -> TaskStatus:
        if completed_hours >= needed_hours:
            return TaskStatus.completed
        if completed_hours > 0:
            return TaskStatus.in_progress
        return TaskStatus.pending
