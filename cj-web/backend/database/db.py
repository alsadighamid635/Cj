"""
SQLite persistence layer for CJ-AI Web.

Design notes:
  - Uses threading.local() so each thread gets its own connection,
    eliminating race conditions under concurrent async/threaded requests.
  - WAL journal mode allows concurrent readers without blocking writers.
  - All public methods are the single source of truth for DB access —
    no raw SQL lives outside this module.

Tables:
  sessions      — chat sessions (id, title, user_id, created_at)
  messages      — individual messages per session
  sources       — RSS feeds and web pages to scrape
  unanswered    — cybersecurity questions with no confident answer
  learning_log  — history of scraping runs
"""

import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger()


def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


class Database:
    """Thread-safe SQLite wrapper using per-thread connections."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._local = threading.local()

    # ── Connection management ──────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        """Return the calling thread's own SQLite connection, creating it if needed."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self._path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
            logger.debug("Opened new SQLite connection for thread %s", threading.current_thread().name)
        return self._local.conn

    def initialize(self) -> None:
        """Create all tables and apply any pending migrations."""
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                title      TEXT    NOT NULL DEFAULT 'New Chat',
                user_id    TEXT    NOT NULL DEFAULT 'anonymous',
                created_at TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                confidence  TEXT    NOT NULL DEFAULT 'high',
                sources     TEXT    NOT NULL DEFAULT '[]',
                timestamp   TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL,
                url          TEXT    NOT NULL UNIQUE,
                type         TEXT    NOT NULL DEFAULT 'rss',
                enabled      INTEGER NOT NULL DEFAULT 1,
                last_fetched TEXT,
                item_count   INTEGER NOT NULL DEFAULT 0,
                added_at     TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS unanswered (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question   TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL,
                reviewed   INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS learning_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT,
                items_added INTEGER,
                timestamp   TEXT NOT NULL
            );
        """)
        conn.commit()
        self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Apply schema migrations idempotently."""
        # v1 → v2: add user_id column to sessions
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'")
            conn.commit()
            logger.info("DB migration: added user_id column to sessions.")
        except sqlite3.OperationalError:
            pass  # Column already exists

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    # ── Sessions ──────────────────────────────────────────────────────────────

    def get_or_create_session(self, session_id: str, user_id: str = "anonymous") -> dict:
        """Return an existing session or insert a new one."""
        conn = self._conn()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO sessions (id, title, user_id, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "New Chat", user_id, _now()),
        )
        conn.commit()
        return {"id": session_id, "title": "New Chat", "user_id": user_id, "created_at": _now()}

    def list_sessions(self, user_id: str = "anonymous") -> list[dict]:
        """Return the 50 most recent sessions belonging to user_id."""
        rows = self._conn().execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def rename_session(self, session_id: str, title: str) -> None:
        conn = self._conn()
        conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()

    def delete_session(self, session_id: str, user_id: str = "anonymous") -> bool:
        """Delete session and its messages. Returns True if the session existed and belonged to user_id."""
        conn = self._conn()
        row = conn.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return True

    def is_first_message(self, session_id: str) -> bool:
        """Return True if no messages exist yet for this session."""
        count = self._conn().execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
        return count == 0

    # ── Messages ──────────────────────────────────────────────────────────────

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        confidence: str = "high",
        sources: str = "[]",
    ) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO messages (session_id, role, content, confidence, sources, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, role, content, confidence, sources, _now()),
        )
        conn.commit()

    def get_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        """Return messages for a session in chronological order."""
        rows = self._conn().execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        result = []
        for r in reversed(rows):
            msg = dict(r)
            raw = msg.get("sources", "[]")
            try:
                msg["sources"] = json.loads(raw) if isinstance(raw, str) else raw
            except (ValueError, TypeError):
                msg["sources"] = []
            result.append(msg)
        return result

    # ── Sources ───────────────────────────────────────────────────────────────

    def list_sources(self) -> list[dict]:
        return [
            dict(r)
            for r in self._conn().execute(
                "SELECT * FROM sources ORDER BY added_at DESC"
            ).fetchall()
        ]

    def add_source(self, name: str, url: str, src_type: str = "rss") -> int | None:
        """Insert a source; returns the new row id, or None if URL already exists."""
        conn = self._conn()
        cur = conn.execute(
            "INSERT OR IGNORE INTO sources (name, url, type, added_at) VALUES (?, ?, ?, ?)",
            (name, url, src_type, _now()),
        )
        conn.commit()
        return cur.lastrowid if cur.lastrowid else None

    def update_source_fetch(self, source_id: int, item_count: int) -> None:
        conn = self._conn()
        conn.execute(
            "UPDATE sources SET last_fetched = ?, item_count = item_count + ? WHERE id = ?",
            (_now(), item_count, source_id),
        )
        conn.commit()

    def delete_source(self, source_id: int) -> None:
        conn = self._conn()
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()

    def toggle_source(self, source_id: int, enabled: bool) -> None:
        conn = self._conn()
        conn.execute("UPDATE sources SET enabled = ? WHERE id = ?", (int(enabled), source_id))
        conn.commit()

    # ── Unanswered ────────────────────────────────────────────────────────────

    def save_unanswered(self, session_id: str, question: str) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO unanswered (session_id, question, timestamp) VALUES (?, ?, ?)",
            (session_id, question, _now()),
        )
        conn.commit()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        conn = self._conn()
        return {
            "sessions":   conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
            "messages":   conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            "sources":    conn.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1").fetchone()[0],
            "unanswered": conn.execute("SELECT COUNT(*) FROM unanswered WHERE reviewed = 0").fetchone()[0],
        }

    def log_learning(self, source_name: str, items_added: int) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO learning_log (source_name, items_added, timestamp) VALUES (?, ?, ?)",
            (source_name, items_added, _now()),
        )
        conn.commit()
