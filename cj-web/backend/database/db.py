import sqlite3
from pathlib import Path
from datetime import datetime


def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def initialize(self):
        self.connect().executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                title      TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                confidence  TEXT DEFAULT 'high',
                sources     TEXT DEFAULT '[]',
                timestamp   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                url         TEXT NOT NULL UNIQUE,
                type        TEXT NOT NULL DEFAULT 'rss',
                enabled     INTEGER NOT NULL DEFAULT 1,
                last_fetched TEXT,
                item_count  INTEGER DEFAULT 0,
                added_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS unanswered (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                question    TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                reviewed    INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS learning_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT,
                items_added INTEGER,
                timestamp   TEXT NOT NULL
            );
        """)
        self._conn.commit()

    # ── Sessions ──────────────────────────────────────────────────────────────

    def get_or_create_session(self, session_id: str) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO sessions(id,title,created_at) VALUES(?,?,?)",
            (session_id, "New Chat", _now()),
        )
        conn.commit()
        return {"id": session_id, "title": "New Chat", "created_at": _now()}

    def list_sessions(self) -> list[dict]:
        rows = self.connect().execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return [dict(r) for r in rows]

    def rename_session(self, session_id: str, title: str):
        conn = self.connect()
        conn.execute("UPDATE sessions SET title=? WHERE id=?", (title, session_id))
        conn.commit()

    def delete_session(self, session_id: str):
        conn = self.connect()
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()

    # ── Messages ──────────────────────────────────────────────────────────────

    def save_message(self, session_id: str, role: str, content: str,
                     confidence: str = "high", sources: str = "[]"):
        conn = self.connect()
        conn.execute(
            "INSERT INTO messages(session_id,role,content,confidence,sources,timestamp) "
            "VALUES(?,?,?,?,?,?)",
            (session_id, role, content, confidence, sources, _now()),
        )
        conn.commit()

    def get_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        rows = self.connect().execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        result = []
        for r in reversed(rows):
            msg = dict(r)
            # sources is stored as JSON string — deserialise it for the API response
            import json as _json
            raw = msg.get("sources", "[]")
            try:
                msg["sources"] = _json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                msg["sources"] = []
            result.append(msg)
        return result

    # ── Sources ───────────────────────────────────────────────────────────────

    def list_sources(self) -> list[dict]:
        return [dict(r) for r in
                self.connect().execute("SELECT * FROM sources ORDER BY added_at DESC").fetchall()]

    def add_source(self, name: str, url: str, src_type: str = "rss") -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT OR IGNORE INTO sources(name,url,type,added_at) VALUES(?,?,?,?)",
            (name, url, src_type, _now()),
        )
        conn.commit()
        return cur.lastrowid

    def update_source_fetch(self, source_id: int, item_count: int):
        conn = self.connect()
        conn.execute(
            "UPDATE sources SET last_fetched=?, item_count=item_count+? WHERE id=?",
            (_now(), item_count, source_id),
        )
        conn.commit()

    def delete_source(self, source_id: int):
        conn = self.connect()
        conn.execute("DELETE FROM sources WHERE id=?", (source_id,))
        conn.commit()

    def toggle_source(self, source_id: int, enabled: bool):
        conn = self.connect()
        conn.execute("UPDATE sources SET enabled=? WHERE id=?", (int(enabled), source_id))
        conn.commit()

    # ── Unanswered ────────────────────────────────────────────────────────────

    def save_unanswered(self, session_id: str, question: str):
        conn = self.connect()
        conn.execute(
            "INSERT INTO unanswered(session_id,question,timestamp) VALUES(?,?,?)",
            (session_id, question, _now()),
        )
        conn.commit()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        conn = self.connect()
        return {
            "sessions":   conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
            "messages":   conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            "sources":    conn.execute("SELECT COUNT(*) FROM sources WHERE enabled=1").fetchone()[0],
            "unanswered": conn.execute("SELECT COUNT(*) FROM unanswered WHERE reviewed=0").fetchone()[0],
        }

    def log_learning(self, source_name: str, items_added: int):
        self.connect().execute(
            "INSERT INTO learning_log(source_name,items_added,timestamp) VALUES(?,?,?)",
            (source_name, items_added, _now()),
        )
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
