"""
PostgreSQL persistence layer for CJ-AI Web.

Design notes:
  - Uses a ThreadedConnectionPool so each thread gets its own connection
    from the pool, eliminating race conditions under concurrent requests.
  - All public methods are the single source of truth for DB access —
    no raw SQL lives outside this module.
  - RealDictCursor makes every row a plain dict, matching the old SQLite API.

Tables:
  users         — registered accounts
  sessions      — chat sessions (id, title, user_id, created_at)
  messages      — individual messages per session
  sources       — RSS feeds and web pages to scrape
  unanswered    — cybersecurity questions with no confident answer
  learning_log  — history of scraping runs
"""

import json
import os
import threading
from datetime import datetime

import psycopg2
import psycopg2.extras
import psycopg2.pool

from utils.logger import get_logger

logger = get_logger()


def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


class Database:
    """Thread-safe PostgreSQL wrapper using a connection pool."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url
        self._pool: psycopg2.pool.ThreadedConnectionPool | None = None
        self._lock = threading.Lock()

    # ── Connection management ──────────────────────────────────────────────────

    def _get_conn(self):
        return self._pool.getconn()

    def _put_conn(self, conn, close: bool = False) -> None:
        self._pool.putconn(conn, close=close)

    def initialize(self) -> None:
        """Create connection pool, all tables, and apply any pending migrations."""
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=self._url,
        )
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id            TEXT PRIMARY KEY,
                            username      TEXT NOT NULL,
                            email         TEXT NOT NULL,
                            password_hash TEXT NOT NULL,
                            created_at    TEXT NOT NULL,
                            UNIQUE (username),
                            UNIQUE (email)
                        );

                        CREATE TABLE IF NOT EXISTS sessions (
                            id         TEXT PRIMARY KEY,
                            title      TEXT NOT NULL DEFAULT 'New Chat',
                            user_id    TEXT NOT NULL DEFAULT 'anonymous',
                            created_at TEXT NOT NULL
                        );

                        CREATE TABLE IF NOT EXISTS messages (
                            id          SERIAL PRIMARY KEY,
                            session_id  TEXT NOT NULL,
                            role        TEXT NOT NULL,
                            content     TEXT NOT NULL,
                            confidence  TEXT NOT NULL DEFAULT 'high',
                            sources     TEXT NOT NULL DEFAULT '[]',
                            timestamp   TEXT NOT NULL
                        );

                        CREATE TABLE IF NOT EXISTS sources (
                            id           SERIAL PRIMARY KEY,
                            name         TEXT NOT NULL,
                            url          TEXT NOT NULL UNIQUE,
                            type         TEXT NOT NULL DEFAULT 'rss',
                            enabled      INTEGER NOT NULL DEFAULT 1,
                            last_fetched TEXT,
                            item_count   INTEGER NOT NULL DEFAULT 0,
                            added_at     TEXT NOT NULL
                        );

                        CREATE TABLE IF NOT EXISTS unanswered (
                            id         SERIAL PRIMARY KEY,
                            session_id TEXT,
                            question   TEXT NOT NULL,
                            timestamp  TEXT NOT NULL,
                            reviewed   INTEGER NOT NULL DEFAULT 0
                        );

                        CREATE TABLE IF NOT EXISTS learning_log (
                            id          SERIAL PRIMARY KEY,
                            source_name TEXT,
                            items_added INTEGER,
                            timestamp   TEXT NOT NULL
                        );
                    """)
            self._migrate(conn)
            logger.info("PostgreSQL database initialised.")
        finally:
            self._put_conn(conn)

    def _migrate(self, conn) -> None:
        """Apply schema migrations idempotently."""
        # Example: add user_id to sessions if missing (already in schema above for new DBs)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        ALTER TABLE sessions
                        ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';
                    """)
            logger.info("DB migration check complete.")
        except Exception as e:
            logger.debug("Migration note: %s", e)

    def close(self) -> None:
        if self._pool:
            self._pool.closeall()

    # ── Sessions ──────────────────────────────────────────────────────────────

    def get_or_create_session(self, session_id: str, user_id: str = "anonymous") -> dict:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
                    row = cur.fetchone()
                    if row:
                        return dict(row)
                    cur.execute(
                        "INSERT INTO sessions (id, title, user_id, created_at) VALUES (%s, %s, %s, %s)",
                        (session_id, "New Chat", user_id, _now()),
                    )
            return {"id": session_id, "title": "New Chat", "user_id": user_id, "created_at": _now()}
        finally:
            self._put_conn(conn)

    def list_sessions(self, user_id: str = "anonymous") -> list[dict]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
                    (user_id,),
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._put_conn(conn)

    def rename_session(self, session_id: str, title: str) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE sessions SET title = %s WHERE id = %s", (title, session_id))
        finally:
            self._put_conn(conn)

    def delete_session(self, session_id: str, user_id: str = "anonymous") -> bool:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM sessions WHERE id = %s AND user_id = %s",
                        (session_id, user_id),
                    )
                    if not cur.fetchone():
                        return False
                    cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
                    cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            return True
        finally:
            self._put_conn(conn)

    def is_first_message(self, session_id: str) -> bool:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM messages WHERE session_id = %s", (session_id,))
                return cur.fetchone()[0] == 0
        finally:
            self._put_conn(conn)

    # ── Users ─────────────────────────────────────────────────────────────────

    def create_user(self, user_id: str, username: str, email: str, password_hash: str) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (id, username, email, password_hash, created_at) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (user_id, username, email, password_hash, _now()),
                    )
        finally:
            self._put_conn(conn)

    def get_user_by_username(self, username: str) -> dict | None:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (username,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            self._put_conn(conn)

    def get_user_by_email(self, email: str) -> dict | None:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            self._put_conn(conn)

    def get_user_by_id(self, user_id: str) -> dict | None:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            self._put_conn(conn)

    def list_all_users(self) -> list[dict]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, username, email, created_at FROM users ORDER BY created_at DESC"
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._put_conn(conn)

    # ── Messages ──────────────────────────────────────────────────────────────

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        confidence: str = "high",
        sources: str = "[]",
    ) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO messages (session_id, role, content, confidence, sources, timestamp) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (session_id, role, content, confidence, sources, _now()),
                    )
        finally:
            self._put_conn(conn)

    def get_messages(self, session_id: str, limit: int = 50, user_id: str | None = None) -> list[dict]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if user_id is not None:
                    cur.execute(
                        "SELECT 1 FROM sessions WHERE id = %s AND user_id = %s",
                        (session_id, user_id),
                    )
                    if not cur.fetchone():
                        return []
                cur.execute(
                    "SELECT * FROM messages WHERE session_id = %s ORDER BY id DESC LIMIT %s",
                    (session_id, limit),
                )
                rows = cur.fetchall()
        finally:
            self._put_conn(conn)

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
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM sources ORDER BY added_at DESC")
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._put_conn(conn)

    def add_source(self, name: str, url: str, src_type: str = "rss") -> int | None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO sources (name, url, type, added_at) VALUES (%s, %s, %s, %s) "
                        "ON CONFLICT (url) DO NOTHING RETURNING id",
                        (name, url, src_type, _now()),
                    )
                    row = cur.fetchone()
                    return row[0] if row else None
        finally:
            self._put_conn(conn)

    def update_source_fetch(self, source_id: int, item_count: int) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE sources SET last_fetched = %s, item_count = item_count + %s WHERE id = %s",
                        (_now(), item_count, source_id),
                    )
        finally:
            self._put_conn(conn)

    def delete_source(self, source_id: int) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sources WHERE id = %s", (source_id,))
        finally:
            self._put_conn(conn)

    def toggle_source(self, source_id: int, enabled: bool) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE sources SET enabled = %s WHERE id = %s",
                        (int(enabled), source_id),
                    )
        finally:
            self._put_conn(conn)

    # ── Unanswered ────────────────────────────────────────────────────────────

    def save_unanswered(self, session_id: str, question: str) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO unanswered (session_id, question, timestamp) VALUES (%s, %s, %s)",
                        (session_id, question, _now()),
                    )
        finally:
            self._put_conn(conn)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sessions")
                sessions = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM messages")
                messages = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1")
                sources = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM unanswered WHERE reviewed = 0")
                unanswered = cur.fetchone()[0]
            return {
                "sessions": sessions,
                "messages": messages,
                "sources": sources,
                "unanswered": unanswered,
            }
        finally:
            self._put_conn(conn)

    def log_learning(self, source_name: str, items_added: int) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO learning_log (source_name, items_added, timestamp) VALUES (%s, %s, %s)",
                        (source_name, items_added, _now()),
                    )
        finally:
            self._put_conn(conn)
