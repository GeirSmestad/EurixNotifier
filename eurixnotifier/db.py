from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MonitoringRow:
    checked_at: datetime
    web_html: str
    sms_content: str
    should_notify: bool
    force_notify: bool
    notified_at: Optional[datetime]


def _ensure_parent_dir(db_path: str) -> None:
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def ensure_db(db_path: str) -> None:
    _ensure_parent_dir(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eurix_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checked_at TEXT NOT NULL,
                web_html TEXT NOT NULL,
                sms_content TEXT NOT NULL,
                should_notify INTEGER NOT NULL,
                force_notify INTEGER NOT NULL,
                notified_at TEXT NULL
            )
            """
        )
        conn.commit()


def insert_monitoring_row(db_path: str, row: MonitoringRow) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO eurix_monitoring (
                checked_at, web_html, sms_content, should_notify, force_notify, notified_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.checked_at.isoformat(),
                row.web_html,
                row.sms_content,
                1 if row.should_notify else 0,
                1 if row.force_notify else 0,
                row.notified_at.isoformat() if row.notified_at else None,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def mark_notified(db_path: str, *, row_id: int, notified_at: datetime) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE eurix_monitoring SET notified_at = ? WHERE id = ?",
            (notified_at.isoformat(), int(row_id)),
        )
        conn.commit()

