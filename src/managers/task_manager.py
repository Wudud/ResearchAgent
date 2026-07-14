from src.managers.base_manager import BaseManager
from src.services.task_service import TaskService
from src.persistence.task_repository import TaskRepository

class TaskManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Task Manager", agent=agent)
        self._service: TaskService | None = None

    def initialize(self):
        super().initialize()
        repo = None
        if self.services:
            repo = self.services.get("task_repo")
            if repo is None and self.config:
                db_path = self.config.get("chat.db_path", "./workspace/chat_history.db")
                repo = TaskRepository(db_path)

        self._service = TaskService(task_repo=repo)

    @property
    def service(self) -> TaskService | None:
        return self._service

        return self._service.create_task(content, priority, source)

    def add_tasks_from_meeting(self, tasks: list[dict]):
        return self._service.create_tasks_batch(tasks, source="Meeting")

    def list_tasks(self, source: str = None, status: str = None):
        return self._service.list_tasks(source, status)

    def complete_task(self, task_id: int):
        self._service.complete_task(task_id)

    def start_task(self, task_id: int):
        self._service.start_task(task_id)

    def delete_task(self, task_id: int):
        self._service.delete_task(task_id)

    def get_stats(self) -> dict:
        return self._service.get_stats()
