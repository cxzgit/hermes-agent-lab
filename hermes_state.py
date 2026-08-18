"""Minimal SQLite session storage for Mini Hermes stage five."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, TypeVar


T = TypeVar("T")
DEFAULT_DB_PATH = Path(__file__).resolve().parent / ".mini-hermes" / "state.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    started_at REAL NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    name TEXT,
    timestamp REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
"""


class SessionDB:
    """Store and restore model-format conversation messages."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._closed = False
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA_SQL)

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._conn.close()
                self._closed = True

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _execute_write(self, fn: Callable[[sqlite3.Connection], T]) -> T:
        """Run all writes in ``fn`` as one atomic transaction."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                result = fn(self._conn)
                self._conn.commit()
                return result
            except BaseException:
                self._conn.rollback()
                raise

    def create_session(self, session_id: str, source: str = "cli") -> str:
        def _do(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT INTO sessions (id, source, started_at) VALUES (?, ?, ?)",
                (session_id, source, time.time()),
            )

        self._execute_write(_do)
        return session_id

    def session_exists(self, session_id: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row is not None

    def append_messages_batch(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
    ) -> int:
        """Append a complete turn; all rows land or none do."""
        if not messages:
            return 0

        def _do(conn: sqlite3.Connection) -> int:
            inserted = 0
            now = time.time()
            for message in messages:
                tool_calls = message.get("tool_calls")
                tool_calls_json = json.dumps(tool_calls) if tool_calls else None
                conn.execute(
                    """INSERT INTO messages (
                           session_id, role, content, tool_call_id,
                           tool_calls, name, timestamp, active
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        session_id,
                        message.get("role", "unknown"),
                        message.get("content"),
                        message.get("tool_call_id"),
                        tool_calls_json,
                        message.get("name") or message.get("tool_name"),
                        now,
                    ),
                )
                inserted += 1
                now += 0.000001
            conn.execute(
                "UPDATE sessions SET message_count = message_count + ? WHERE id = ?",
                (inserted, session_id),
            )
            return inserted

        return self._execute_write(_do)

    def get_messages_as_conversation(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Restore active rows in true insertion order."""
        with self._lock:
            rows = self._conn.execute(
                """SELECT role, content, tool_call_id, tool_calls, name
                   FROM messages
                   WHERE session_id = ? AND active = 1
                   ORDER BY id""",
                (session_id,),
            ).fetchall()

        messages: list[dict[str, Any]] = []
        for row in rows:
            message: dict[str, Any] = {
                "role": row["role"],
                "content": row["content"],
            }
            if row["tool_call_id"]:
                message["tool_call_id"] = row["tool_call_id"]
            if row["tool_calls"]:
                message["tool_calls"] = json.loads(row["tool_calls"])
            if row["name"]:
                message["name"] = row["name"]
            messages.append(message)
        return messages
