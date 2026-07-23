"""Durable SQLite ledger for portfolio decisions and planned tickets."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .execution import ReconciliationResult


class ExecutionLedger:
    """Append-only decision ledger suitable for paper and dry-run evidence."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    equity REAL NOT NULL,
                    execution_phase TEXT NOT NULL,
                    target_payload TEXT NOT NULL,
                    deferred_payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    notional REAL NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    FOREIGN KEY(cycle_id) REFERENCES execution_cycles(id)
                )
                """
            )

    def record(self, result: ReconciliationResult, mode: str = "dry_run") -> int:
        if mode not in {"paper", "dry_run", "live"}:
            raise ValueError("mode must be paper, dry_run, or live")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO execution_cycles(
                    created_at, mode, policy_id, equity, execution_phase,
                    target_payload, deferred_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    mode,
                    result.policy_id,
                    result.equity,
                    result.execution_phase,
                    json.dumps(dict(result.target_weights), sort_keys=True),
                    json.dumps(list(result.deferred), sort_keys=True),
                ),
            )
            cycle_id = int(cursor.lastrowid)
            for ticket in result.executable_tickets:
                connection.execute(
                    """
                    INSERT INTO execution_tickets(
                        cycle_id, symbol, side, quantity, notional, status, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cycle_id,
                        ticket.symbol,
                        ticket.side,
                        ticket.quantity,
                        ticket.notional,
                        ticket.status,
                        ticket.reason,
                    ),
                )
        return cycle_id

    def recent_cycles(self, limit: int = 20) -> list[dict]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, created_at, mode, policy_id, equity, execution_phase,
                       target_payload, deferred_payload
                FROM execution_cycles
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                **dict(row),
                "target_payload": json.loads(row["target_payload"]),
                "deferred_payload": json.loads(row["deferred_payload"]),
            }
            for row in rows
        ]

    def tickets_for_cycle(self, cycle_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol, side, quantity, notional, status, reason
                FROM execution_tickets
                WHERE cycle_id = ?
                ORDER BY id
                """,
                (cycle_id,),
            ).fetchall()
        return [dict(row) for row in rows]
