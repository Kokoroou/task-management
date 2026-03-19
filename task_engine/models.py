"""Data models for Work State Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    TODO = "TODO"
    ACTIVE = "ACTIVE"
    INTERRUPTED = "INTERRUPTED"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    DROPPED = "DROPPED"


@dataclass
class Task:
    id: int
    title: str
    state: TaskState
    parent_id: Optional[int] = None
    next_step: Optional[str] = None
    block_reason: Optional[str] = None
    follow_up_at: Optional[datetime] = None
    last_alerted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: dict) -> "Task":
        """Create a Task from a sqlite3.Row or dict."""
        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            if val is None:
                return None
            return datetime.fromisoformat(val)

        return cls(
            id=row["id"],
            title=row["title"],
            state=TaskState(row["state"]),
            parent_id=row["parent_id"],
            next_step=row["next_step"],
            block_reason=row["block_reason"],
            follow_up_at=parse_dt(row["follow_up_at"]),
            last_alerted_at=parse_dt(row["last_alerted_at"]),
            created_at=parse_dt(row["created_at"]) or datetime.now(),
            updated_at=parse_dt(row["updated_at"]) or datetime.now(),
        )
