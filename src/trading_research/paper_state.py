from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class PaperStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def load(self) -> dict:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("SELECT key, value FROM state").fetchall()
        state = {key: json.loads(value) for key, value in rows}
        state.setdefault("cash", 10_000.0)
        state.setdefault("positions", {})
        return state

    def save(self, state: dict) -> None:
        with sqlite3.connect(self.path) as conn:
            for key, value in state.items():
                conn.execute(
                    "INSERT OR REPLACE INTO state(key, value) VALUES (?, ?)",
                    (key, json.dumps(value)),
                )

    def log_event(self, event_type: str, payload: dict) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO events(created_at, event_type, payload) VALUES (?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), event_type, json.dumps(payload, sort_keys=True)),
            )
