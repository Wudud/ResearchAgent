"""
任务仓库模块 - 任务数据的SQLite持久化存储。

存储任务定义、状态追踪和执行历史。
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class TaskRepository:
    """任务仓库 - 管理任务数据的SQLite存储。

    Attributes:
        _db_path: 数据库文件路径
    """

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.TaskRepository")
        self._persistent_conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if str(self._db_path) == ":memory:":
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(":memory:")
                self._persistent_conn.execute("PRAGMA foreign_keys = ON")
                self._persistent_conn.row_factory = sqlite3.Row
            return self._persistent_conn
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    priority TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    source TEXT DEFAULT '',
                    deadline TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT ''
                );
            """)

    def create_task(self, content: str, priority: str = "medium",
                    source: str = "", deadline: str = "", status: str = "pending") -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (content, priority, status, source, deadline, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (content, priority, status, source, deadline, now)
            )
        self._logger.info(f"Created task: {cursor.lastrowid}")
        return cursor.lastrowid
        return cursor.lastrowid

    def get_task(self, task_id: int) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

    def list_tasks(self, source: str = None, status: str = None, limit: int = 100) -> list[dict]:
        with self._get_conn() as conn:
            conditions = []
            params = []
            if source:
                conditions.append("source = ?")
                params.append(source)
            if status:
                conditions.append("status = ?")
                params.append(status)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM tasks{where} ORDER BY created_at DESC LIMIT ?", params
            ).fetchall()
        return [dict(r) for r in rows]

    def update_task(self, task_id: int, **kwargs):
        if not kwargs:
            return
        with self._get_conn() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in kwargs)
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                (*kwargs.values(), task_id)
            )

    def complete_task(self, task_id: int):
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET status = '', completed_at = ? WHERE id = ?",
                (now, task_id)
            )

    def delete_task(self, task_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._logger.info(f"Deleted task: {task_id}")

    # --- 旧API别名 ---

    def create(self, task) -> object:
        task_id = self.create_task(
            content=getattr(task, 'content', ''),
            priority=getattr(task, 'priority', 'medium'),
            source=getattr(task, 'source', ''),
            deadline=getattr(task, 'deadline', ''),
            status=getattr(task, 'status', 'pending'),
        )
        task.id = task_id
        return task

    def get(self, task_id: int):
        return self.get_task(task_id)

    def list_all(self, source: str = None, status: str = None):
        return self.list_tasks(source=source, status=status)

    def update_status(self, task_id: int, status: str):
        self.update_task(task_id, status=status)
        if status == 'completed':
            self.complete_task(task_id)

    def delete(self, task_id: int):
        self.delete_task(task_id)
