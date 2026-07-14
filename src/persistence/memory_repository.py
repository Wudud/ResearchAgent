"""
记忆仓库模块 - 研究记忆的SQLite持久化存储。

存储经验、见解和知识片段供长期检索。
"""

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ResearchMemory:
    """研究记忆数据类 - 表示一条研究经验或知识片段。

    Attributes:
        id: 唯一标识符
        category: 分类（Meeting/Paper/Dataset/Experiment/Research）
        title: 记忆标题
        content: 记忆内容
        source: 来源描述
        importance: 重要程度
        created_at: 创建时间
    """
    id: str = ""
    category: str = ""
    title: str = ""
    content: str = ""
    source: str = ""
    importance: str = ""
    created_at: str = ""


class ResearchMemoryRepository:
    """研究记忆仓库 - 管理研究记忆的SQLite存储。

    Attributes:
        _db_path: 数据库文件路径
    """

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.ResearchMemoryRepository")
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
                CREATE TABLE IF NOT EXISTS research_memory (
                    id TEXT PRIMARY KEY,
                    category TEXT DEFAULT '',
                    title TEXT DEFAULT '',
                    content TEXT DEFAULT '',
                    source TEXT DEFAULT '',
                    importance TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
            """)

    def save_memory(self, category: str, title: str, content: str,
                    source: str = "", importance: str = "") -> str:
        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO research_memory (id, category, title, content, source, importance, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (memory_id, category, title, content, source, importance, now)
            )
        self._logger.info(f"Saved memory: {memory_id}")
        return memory_id

    def get_memory(self, memory_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM research_memory WHERE id = ?", (memory_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_memories(self, category: str = None, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM research_memory WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                    (category, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM research_memory ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    def search_memories(self, keyword: str, limit: int = 10) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM research_memory WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{keyword}%", f"%{keyword}%", limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_memory(self, memory_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM research_memory WHERE id = ?", (memory_id,))
        self._logger.info(f"Deleted memory: {memory_id}")

    # --- 旧API别名 ---

    def save(self, mem) -> object:
        mem.id = self.save_memory(
            category=getattr(mem, 'category', ''),
            title=getattr(mem, 'title', ''),
            content=getattr(mem, 'content', ''),
            source=getattr(mem, 'source', ''),
            importance=getattr(mem, 'importance', ''),
        )
        return mem

    def get(self, memory_id: str):
        return self.get_memory(memory_id)

    def list_by_category(self, category: str):
        return self.list_memories(category=category)

    def search(self, keyword: str):
        return self.search_memories(keyword)
