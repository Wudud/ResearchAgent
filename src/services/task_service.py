"""
任务服务模块 - 任务管理的核心服务实现。

提供任务调度、进度追踪和依赖管理功能。
"""

import logging

from src.task.models import Task
from src.persistence.task_repository import TaskRepository


class TaskService:
    """任务服务 - 任务管理的核心业务逻辑。

    Attributes:
        _repo: 任务仓库
    """

    def __init__(self, task_repo: TaskRepository = None):
        self._repo = task_repo
        self._logger = logging.getLogger("ResearchAgent.TaskService")

    def create_task(self, content: str, source: str = "",
                    priority: str = "medium", deadline: str = "",
                    status: str = "pending") -> Task:
        """创建单个任务。

        Args:
            content: 任务内容
            source: 来源标识
            priority: 优先级
            deadline: 截止日期
            status: 初始状态

        Returns:
            Task: 创建的任务对象
        """
        if self._repo is None:
            raise RuntimeError("TaskRepository not configured")
        task = Task(
            content=content,
            priority=priority,
            source=source,
            deadline=deadline,
            status=status,
        )
        return self._repo.create(task)

    def create_tasks_batch(self, tasks: list[dict], source: str = "") -> list[Task]:
        """批量创建任务。

        Args:
            tasks: 任务字典列表
            source: 来源标识

        Returns:
            list[Task]: 创建的任务列表
        """
        results = []
        for t in tasks:
            task = self.create_task(
                content=t.get("content", ""),
                priority=t.get("priority", "medium"),
                source=source,
                deadline=t.get("deadline", ""),
            )
            results.append(task)
        return results

    def get_task(self, task_id: int) -> dict | None:
        """获取单个任务。

        Args:
            task_id: 任务ID

        Returns:
            dict: 任务数据
        """
        return self._repo.get_task(task_id)

    def list_tasks(self, source: str = None, status: str = None) -> list[dict]:
        """列出任务。

        Args:
            source: 来源过滤
            status: 状态过滤

        Returns:
            list[dict]: 任务列表
        """
        return self._repo.list_tasks(source=source, status=status)

    def update_status(self, task_id: int, status: str):
        """更新任务状态。

        Args:
            task_id: 任务ID
            status: 新状态
        """
        self._repo.update_task(task_id, status=status)

    def complete_task(self, task_id: int):
        """完成任务。

        Args:
            task_id: 任务ID
        """
        self._repo.complete_task(task_id)

    def start_task(self, task_id: int):
        """开始任务。

        Args:
            task_id: 任务ID
        """
        self._repo.update_task(task_id, status="in_progress")

    def delete_task(self, task_id: int):
        """删除任务。

        Args:
            task_id: 任务ID
        """
        self._repo.delete_task(task_id)

    def get_stats(self) -> dict:
        """获取任务统计数据。

        Returns:
            dict: 包含total、completed、in_progress、pending的统计信息
        """
        all_tasks = self._repo.list_tasks()
        total = len(all_tasks)
        completed = sum(1 for t in all_tasks if t.get("status") == "completed")
        in_progress = sum(1 for t in all_tasks if t.get("status") == "in_progress")
        pending = total - completed - in_progress
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": f"{completed / total * 100:.0f}%" if total > 0 else "0%",
        }
