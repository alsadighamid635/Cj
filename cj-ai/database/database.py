import sqlite3
from pathlib import Path
from datetime import datetime
from utils.helpers import now_iso
from utils.logger import get_logger

logger = get_logger()


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def initialize(self):
        conn = self.connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    NOT NULL UNIQUE,
                created_at TEXT   NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
                content    TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS unanswered (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                question   TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL,
                reviewed   INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                level     TEXT NOT NULL,
                message   TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
        """)
        conn.commit()
        logger.debug("Database initialized at %s", self.db_path)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_or_create_user(self, username: str) -> int:
        conn = self.connect()
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, now_iso()),
        )
        conn.commit()
        return cursor.lastrowid

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def save_message(self, user_id: int, role: str, content: str):
        conn = self.connect()
        conn.execute(
            "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, now_iso()),
        )
        conn.commit()

    def get_recent_messages(self, user_id: int, limit: int = 20) -> list[dict]:
        conn = self.connect()
        rows = conn.execute(
            """SELECT role, content, timestamp FROM messages
               WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ------------------------------------------------------------------
    # Unanswered questions
    # ------------------------------------------------------------------

    def save_unanswered(self, user_id: int, question: str):
        conn = self.connect()
        conn.execute(
            "INSERT INTO unanswered (user_id, question, timestamp) VALUES (?, ?, ?)",
            (user_id, question, now_iso()),
        )
        conn.commit()
        logger.info("Unanswered question saved: %s", question[:80])

    def get_unreviewed(self) -> list[dict]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM unanswered WHERE reviewed = 0 ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_reviewed(self, question_id: int):
        conn = self.connect()
        conn.execute(
            "UPDATE unanswered SET reviewed = 1 WHERE id = ?", (question_id,)
        )
        conn.commit()

    # ------------------------------------------------------------------
    # System logs
    # ------------------------------------------------------------------

    def save_log(self, level: str, message: str):
        conn = self.connect()
        conn.execute(
            "INSERT INTO logs (level, message, timestamp) VALUES (?, ?, ?)",
            (level, message, now_iso()),
        )
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
