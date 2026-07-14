"""
论文仓库模块 - 论文数据的SQLite持久化存储。

存储论文元信息、全文内容和引用数据。
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class PaperRepository:
    """论文仓库 - 管理论文数据的SQLite存储。

    Attributes:
        _db_path: 数据库文件路径
    """

    def __init__(self, db_path: str = "workspace/chat_history.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("ResearchAgent.PaperRepository")
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
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    authors TEXT DEFAULT '',
                    abstract TEXT DEFAULT '',
                    sections TEXT DEFAULT '[]',
                    keywords TEXT DEFAULT '[]',
                    summary TEXT DEFAULT '',
                    contributions TEXT DEFAULT '[]',
                    methodology TEXT DEFAULT '',
                    limitations TEXT DEFAULT '',
                    future_work TEXT DEFAULT '',
                    reference TEXT DEFAULT '',
                    file_path TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
            """)

    def create_paper(self, title: str, authors: str = "", abstract: str = "",
                     keywords: list = None, file_path: str = "") -> str:
        paper_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO papers (id, title, authors, abstract, keywords, file_path, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (paper_id, title, authors, abstract, json.dumps(keywords or []), file_path, now)
            )
        self._logger.info(f"Created paper: {paper_id}")
        return paper_id

    def get_paper(self, paper_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        return dict(row) if row else None

    def list_papers(self, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM papers ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def update_paper(self, paper_id: str, **kwargs):
        if not kwargs:
            return
        with self._get_conn() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in kwargs)
            conn.execute(
                f"UPDATE papers SET {set_clause} WHERE id = ?",
                (*kwargs.values(), paper_id)
            )

    def delete_paper(self, paper_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        self._logger.info(f"Deleted paper: {paper_id}")

    # --- 旧API别名 ---

    def save(self, paper) -> object:
        keywords = getattr(paper, 'keywords', None)
        if isinstance(keywords, list):
            keywords = json.dumps(keywords)
        elif keywords is None:
            keywords = '[]'
        paper_id = self.create_paper(
            title=getattr(paper, 'title', ''),
            authors=getattr(paper, 'authors', ''),
            abstract=getattr(paper, 'abstract', ''),
            keywords=keywords,
            file_path=getattr(paper, 'file_path', ''),
        )
        paper.id = paper_id
        return paper

    def get(self, paper_id: str):
        data = self.get_paper(paper_id)
        if data is None:
            return None
        return self._row_to_obj(data)

    def search(self, query: str) -> list:
        results = self.list_papers()
        return [self._row_to_obj(r) for r in results if query.lower() in r.get('title', '').lower()]

    def _row_to_obj(self, data: dict):
        p = type('Paper', (), {})()
        p.id = data.get('id', '')
        p.title = data.get('title', '')
        p.authors = data.get('authors', '')
        p.abstract = data.get('abstract', '')
        p.keywords = json.loads(data.get('keywords', '[]')) if isinstance(data.get('keywords'), str) else (data.get('keywords') or [])
        p.summary = data.get('summary', '')
        p.contributions = json.loads(data.get('contributions', '[]')) if isinstance(data.get('contributions'), str) else (data.get('contributions') or [])
        p.methodology = data.get('methodology', '')
        p.limitations = data.get('limitations', '')
        p.future_work = data.get('future_work', '')
        p.reference = data.get('reference', '')
        p.file_path = data.get('file_path', '')
        p.created_at = data.get('created_at', '')
        return p
        results = self.list_papers()
        return [r for r in results if query.lower() in r.get('title', '').lower()]
