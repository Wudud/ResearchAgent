"""
会议仓库模块 - 会议数据的SQLite持久化存储。

存储会议记录、转录和摘要信息。
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class MeetingRepository:
    """会议仓库 - 管理会议数据的SQLite存储。

    Attributes:
        _db_path: 数据库文件路径
    """

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.MeetingRepository")
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
                CREATE TABLE IF NOT EXISTS meetings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    transcript TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    discussion TEXT DEFAULT '',
                    decision TEXT DEFAULT '',
                    suggestions TEXT DEFAULT '[]',
                    next_step TEXT DEFAULT '',
                    conversation_id TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
            """)

    def create_meeting(self, title: str, transcript: str = "", summary: str = "",
                       discussion: str = "", decision: str = "",
                       suggestions: list = None, next_step: str = "") -> str:
        meeting_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO meetings (id, title, transcript, summary, discussion, decision, suggestions, next_step, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (meeting_id, title, transcript, summary, discussion, decision,
                 json.dumps(suggestions or []), next_step, now)
            )
        self._logger.info(f"Created meeting: {meeting_id}")
        return meeting_id

    def get_meeting(self, meeting_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return dict(row) if row else None

    def list_meetings(self, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM meetings ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def update_meeting(self, meeting_id: str, **kwargs):
        if not kwargs:
            return
        with self._get_conn() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in kwargs)
            conn.execute(
                f"UPDATE meetings SET {set_clause} WHERE id = ?",
                (*kwargs.values(), meeting_id)
            )

    def delete_meeting(self, meeting_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        self._logger.info(f"Deleted meeting: {meeting_id}")

    # --- 旧API别名（向后兼容） ---

    def save(self, meeting) -> object:
        meeting_id = self.create_meeting(
            title=getattr(meeting, 'title', ''),
            transcript=getattr(meeting, 'transcript', ''),
            summary=getattr(meeting, 'summary', ''),
        )
        meeting.id = meeting_id
        meeting.created_at = getattr(meeting, 'created_at', '') or ''
        return meeting

    def get(self, meeting_id: str):
        data = self.get_meeting(meeting_id)
        if data is None:
            return None
        return self._row_to_obj(data)

    def list_all(self):
        return [self._row_to_obj(d) for d in self.list_meetings()]

    def _row_to_obj(self, data: dict):
        m = type('Meeting', (), {})()
        m.id = data.get('id', '')
        m.title = data.get('title', '')
        m.transcript = data.get('transcript', '')
        m.summary = data.get('summary', '')
        m.discussion = data.get('discussion', '')
        m.decision = data.get('decision', '')
        m.suggestions = json.loads(data.get('suggestions', '[]')) if isinstance(data.get('suggestions'), str) else (data.get('suggestions') or [])
        m.next_step = data.get('next_step', '')
        m.conversation_id = data.get('conversation_id', '')
        m.created_at = data.get('created_at', '')
        return m

    def delete(self, meeting_id: str):
        self.delete_meeting(meeting_id)
