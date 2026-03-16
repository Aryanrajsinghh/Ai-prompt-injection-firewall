"""SQLite logging utilities for prompt firewall events."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from backend.config import settings


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attack_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT,
    attack_type TEXT,
    risk_score REAL,
    decision TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db() -> None:
    """Initialize the SQLite database schema.

    Called once at application startup via the lifespan handler in main.py.
    Do not call this inside individual query functions.
    """
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(CREATE_TABLE_SQL)
        connection.commit()


def log_attack(
    prompt: str,
    attack_type: str,
    risk_score: float,
    decision: str,
) -> None:
    """Persist an analyzed prompt event."""
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            """
            INSERT INTO attack_logs (prompt, attack_type, risk_score, decision)
            VALUES (?, ?, ?, ?)
            """,
            (prompt, attack_type, risk_score, decision),
        )
        connection.commit()


def get_all_logs(limit: int | None = None) -> List[Dict[str, Any]]:
    """Return logged attack events ordered by most recent first."""
    query = """
        SELECT id, prompt, attack_type, risk_score, decision, timestamp
        FROM attack_logs
        ORDER BY id DESC
    """
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    with sqlite3.connect(settings.database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]
