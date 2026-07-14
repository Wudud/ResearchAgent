"""
实验仓库模块 - 实验数据的SQLite持久化存储。

提供实验定义、运行记录和指标的完整存储。
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ExperimentRepository:
    """实验仓库 - 管理实验数据的SQLite存储。"""

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.ExperimentRepository")
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
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    description TEXT DEFAULT '',
                    dataset TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    parameters TEXT DEFAULT '{}',
                    metrics TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'created',
                    log_path TEXT DEFAULT '',
                    checkpoint_path TEXT DEFAULT '',
                    tensorboard_path TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT ''
                );
            """)

    def create(self, exp) -> object:
        """创建实验（接受Experiment对象）。"""
        now = datetime.now(timezone.utc).isoformat()
        params = json.dumps(getattr(exp, 'parameters', None) or {})
        metrics = json.dumps(getattr(exp, 'metrics', None) or [])
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO experiments (name, description, dataset, model, parameters, metrics, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (getattr(exp, 'name', ''), getattr(exp, 'description', ''),
                 getattr(exp, 'dataset', ''), getattr(exp, 'model', ''),
                 params, metrics, getattr(exp, 'status', 'created'), now, now)
            )
            exp.id = cursor.lastrowid
            exp.created_at = now
            exp.updated_at = now
            exp.parameters = getattr(exp, 'parameters', None) or {}
            exp.metrics = getattr(exp, 'metrics', None) or []
            exp.status = getattr(exp, 'status', 'created')
        return exp

    def get(self, exp_id: int):
        """获取实验。"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_exp(row)

    def list_all(self, status: str = None) -> list:
        """列出实验，可按状态过滤。"""
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM experiments WHERE status = ? ORDER BY updated_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM experiments ORDER BY updated_at DESC").fetchall()
        return [self._row_to_exp(r) for r in rows]

    def list_by_status(self, status: str) -> list:
        """按状态列出实验。"""
        return self.list_all(status=status)

    def update(self, *args, **kwargs):
        """更新实验字段。支持 update(exp_id, **kwargs) 或 update(exp_object)。"""
        if len(args) == 1 and hasattr(args[0], 'id'):
            exp = args[0]
            exp_id = exp.id
            now = datetime.now(timezone.utc).isoformat()
            updates = {"updated_at": now}
            for attr in ('name', 'description', 'dataset', 'model', 'status', 'notes',
                         'log_path', 'checkpoint_path', 'tensorboard_path'):
                if hasattr(exp, attr):
                    val = getattr(exp, attr)
                    if val is not None:
                        updates[attr] = val
            if hasattr(exp, 'parameters') and exp.parameters is not None:
                updates['parameters'] = json.dumps(exp.parameters) if not isinstance(exp.parameters, str) else exp.parameters
            if hasattr(exp, 'metrics') and exp.metrics is not None:
                updates['metrics'] = json.dumps(exp.metrics) if not isinstance(exp.metrics, str) else exp.metrics
        else:
            exp_id = args[0] if args else kwargs.pop('exp_id', None)
            now = datetime.now(timezone.utc).isoformat()
            updates = {**kwargs, "updated_at": now}
        with self._get_conn() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(f"UPDATE experiments SET {set_clause} WHERE id = ?", (*updates.values(), exp_id))

    def update_status(self, exp_id: int, status: str):
        """更新实验状态。"""
        now = datetime.now(timezone.utc).isoformat()
        updates = {"status": status, "updated_at": now}
        if status == "completed":
            updates["completed_at"] = now
        self.update(exp_id, **updates)

    def delete(self, exp_id: int):
        """删除实验。"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))

    def _row_to_exp(self, row) -> object:
        """将数据库行转换为Experiment对象。"""
        exp = type('Experiment', (), {})()
        exp.id = row["id"]
        exp.name = row["name"]
        exp.description = row["description"] or ""
        exp.dataset = row["dataset"] or ""
        exp.model = row["model"] or ""
        exp.parameters = json.loads(row["parameters"]) if row["parameters"] else {}
        exp.metrics = json.loads(row["metrics"]) if row["metrics"] else []
        exp.status = row["status"] or "created"
        exp.log_path = row["log_path"] or ""
        exp.checkpoint_path = row["checkpoint_path"] or ""
        exp.tensorboard_path = row["tensorboard_path"] or ""
        exp.notes = row["notes"] or ""
        exp.created_at = row["created_at"]
        exp.updated_at = row["updated_at"]
        exp.completed_at = row["completed_at"] or ""
        return exp
