"""
对话仓库模块 - 对话数据的SQLite持久化存储。

提供对话和消息的CRUD操作及事务管理。
支持内存数据库和文件数据库两种模式。
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class ConversationRepository:
    """对话仓库 - 管理对话和消息的SQLite存储。

    提供对话的创建、查询、更新、删除以及消息的完整管理功能。

    Attributes:
        _db_path: 数据库文件路径
        _persistent_conn: 内存数据库的持久连接
    """

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.ConversationRepository")
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
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    attachments TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id) ON DELETE CASCADE
                );
            """)

    def create_conversation(self, title: str = "") -> str:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, now, now)
            )
        self._logger.info(f"Created conversation: {conv_id}")
        return conv_id

    def get_conversation(self, conv_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_conversations(self, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_title(self, conv_id: str, title: str):
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id)
            )

    def delete_conversation(self, conv_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        self._logger.info(f"Deleted conversation: {conv_id}")

    def add_message(self, conv_id: str, role: str, content: str,
                    msg_type: str = "text", attachments=None,
                    metadata=None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        if isinstance(attachments, list):
            attachments = json.dumps(attachments)
        elif attachments is None:
            attachments = "[]"
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        elif metadata is None:
            metadata = "{}"
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO messages (conversation_id, role, content, message_type, attachments, metadata, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (conv_id, role, content, msg_type, attachments, metadata, now)
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conv_id)
            )
        return cursor.lastrowid

    def get_messages(self, conv_id: str) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC",
                (conv_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def clear_messages(self, conv_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
