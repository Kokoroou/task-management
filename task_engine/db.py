"""SQLite database layer for Work State Engine."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from task_engine.models import Task, TaskState

DB_PATH = Path.home() / ".task_engine.db"


def get_db_path() -> Path:
    """Return the database file path."""
    return DB_PATH


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connection with Row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and indexes if they don't exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT    NOT NULL,
                state          TEXT    NOT NULL DEFAULT 'TODO',
                parent_id      INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                next_step      TEXT,
                block_reason   TEXT,
                follow_up_at   TEXT,
                last_alerted_at TEXT,
                created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON tasks(state)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON tasks(parent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_follow_up ON tasks(follow_up_at)")


# ─────────────────────────────── CRUD ────────────────────────────────


def insert_task(title: str, parent_id: Optional[int] = None) -> Task:
    """Insert a new TODO task and return it."""
    with get_conn() as conn:
        now = _now()
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, state, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, TaskState.TODO.value, parent_id, now, now),
        )
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return Task.from_row(dict(row))


def fetch_task(task_id: int) -> Optional[Task]:
    """Fetch a single task by ID."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return Task.from_row(dict(row)) if row else None


def fetch_all_tasks(exclude_states: Optional[List[TaskState]] = None) -> List[Task]:
    """Fetch all tasks, optionally excluding tasks with given states."""
    with get_conn() as conn:
        if exclude_states:
            placeholders = ", ".join("?" for _ in exclude_states)
            rows = conn.execute(
                f"SELECT * FROM tasks WHERE state NOT IN ({placeholders}) ORDER BY id",
                [s.value for s in exclude_states],
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return [Task.from_row(dict(r)) for r in rows]


def fetch_by_state(state: TaskState) -> List[Task]:
    """Fetch all tasks with a given state."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE state = ? ORDER BY id",
            (state.value,),
        ).fetchall()
        return [Task.from_row(dict(r)) for r in rows]


def update_task(task_id: int, **kwargs) -> Optional[Task]:
    """Generic update: pass column=value keyword arguments."""
    if not kwargs:
        return fetch_task(task_id)

    kwargs["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]

    with get_conn() as conn:
        conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return Task.from_row(dict(row)) if row else None


def fetch_due_followups() -> List[Task]:
    """Return BLOCKED tasks whose follow_up_at <= now and not recently alerted."""
    now = _now()
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE state = ?
              AND follow_up_at IS NOT NULL
              AND follow_up_at <= ?
              AND (last_alerted_at IS NULL OR last_alerted_at < follow_up_at)
            ORDER BY follow_up_at
            """,
            (TaskState.BLOCKED.value, now),
        ).fetchall()
        return [Task.from_row(dict(r)) for r in rows]


def mark_alerted(task_id: int) -> None:
    """Update last_alerted_at to now."""
    update_task(task_id, last_alerted_at=_now())


# ─────────────────────────── helpers ─────────────────────────────────


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")
