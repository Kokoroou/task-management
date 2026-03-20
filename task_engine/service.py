"""Business logic / state-machine for Work State Engine."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from task_engine import db
from task_engine.models import Task, TaskState


class WSEError(Exception):
    """Domain-level error (shown to user without traceback)."""


# ──────────────────────────── add ────────────────────────────────────


def add_task(title: str, parent_id: Optional[int] = None) -> Task:
    """Create a new task in TODO state."""
    if parent_id is not None:
        parent = db.fetch_task(parent_id)
        if parent is None:
            raise WSEError(f"Parent task #{parent_id} not found.")
    return db.insert_task(title, parent_id=parent_id)


# ──────────────────────────── query ──────────────────────────────────


def get_active() -> Optional[Task]:
    """Return the single ACTIVE task, or None."""
    tasks = db.fetch_by_state(TaskState.ACTIVE)
    return tasks[0] if tasks else None


def next_task() -> Optional[Task]:
    """
    Return the best task to work on next:
      1. ACTIVE task (already running)
      2. Most-recently-updated INTERRUPTED task
      3. Oldest TODO task
    """
    active = get_active()
    if active:
        return active

    interrupted = db.fetch_by_state(TaskState.INTERRUPTED)
    if interrupted:
        return max(interrupted, key=lambda t: t.updated_at)

    todos = db.fetch_by_state(TaskState.TODO)
    if todos:
        return todos[0]  # oldest by id

    return None


def list_tasks(all_tasks: bool = False) -> List[Task]:
    """Return tasks (exclude DONE and DROPPED by default)."""
    if all_tasks:
        return db.fetch_all_tasks()
    return db.fetch_all_tasks(exclude_states=[TaskState.DONE, TaskState.DROPPED])


# ──────────────────────────── start ──────────────────────────────────


def start_task(task_id: int, next_step_for_current: Optional[str] = None) -> Tuple[Optional[Task], Task]:
    """
    Start a task:
    - If another task is currently ACTIVE, interrupt it first.
      `next_step_for_current` is required in that case.
    - Returns (interrupted_task | None, newly_active_task).
    """
    task = db.fetch_task(task_id)
    if task is None:
        raise WSEError(f"Task #{task_id} not found.")
    if task.state == TaskState.DONE:
        raise WSEError(f"Task #{task_id} is already DONE — cannot start it.")
    if task.state == TaskState.DROPPED:
        raise WSEError(f"Task #{task_id} is DROPPED — cannot start it.")
    if task.state == TaskState.ACTIVE:
        raise WSEError(f"Task #{task_id} is already ACTIVE.")

    # Interrupt current active task
    current_active = get_active()
    interrupted: Optional[Task] = None

    if current_active and current_active.id != task_id:
        if not next_step_for_current:
            raise WSEError(
                f'Task #{current_active.id} "{current_active.title}" is currently ACTIVE.\n'
                "You must provide a --next-step before switching tasks.\n"
                "Example: task start {task_id} --next-step \"Where I left off...\""
            )
        interrupted = db.update_task(
            current_active.id,
            state=TaskState.INTERRUPTED.value,
            next_step=next_step_for_current,
        )

    # Activate requested task
    active = db.update_task(task_id, state=TaskState.ACTIVE.value)
    return interrupted, active


# ──────────────────────────── update ─────────────────────────────────


def update_task_fields(
    task_id: int,
    next_step: Optional[str] = None,
    block_reason: Optional[str] = None,
) -> Task:
    """Update mutable fields of a task (next_step, block_reason) without changing state."""
    task = db.fetch_task(task_id)
    if task is None:
        raise WSEError(f"Task #{task_id} not found.")
    if task.state in (TaskState.DONE, TaskState.DROPPED):
        raise WSEError(f"Task #{task_id} is {task.state.value} — cannot update it.")

    updates: dict = {}
    if next_step is not None:
        updates["next_step"] = next_step if next_step != "" else None
    if block_reason is not None:
        updates["block_reason"] = block_reason if block_reason != "" else None

    if not updates:
        return task

    return db.update_task(task_id, **updates)


# ──────────────────────────── done ───────────────────────────────────


def done_task(task_id: int) -> Tuple[Task, Optional[Task]]:
    """
    Mark task as DONE.
    Returns (done_task, suggested_next_task).
    If it was a sub-task, suggest the parent (if INTERRUPTED or TODO).
    """
    task = db.fetch_task(task_id)
    if task is None:
        raise WSEError(f"Task #{task_id} not found.")
    if task.state == TaskState.DONE:
        raise WSEError(f"Task #{task_id} is already DONE.")
    if task.state == TaskState.DROPPED:
        raise WSEError(f"Task #{task_id} is DROPPED — cannot mark it done.")

    done = db.update_task(task_id, state=TaskState.DONE.value, next_step=None)

    # Suggest parent if it exists and is not done
    suggestion: Optional[Task] = None
    if task.parent_id:
        parent = db.fetch_task(task.parent_id)
        if parent and parent.state != TaskState.DONE:
            suggestion = parent

    # Otherwise suggest the generic next task
    if suggestion is None:
        suggestion = next_task()
        # Don't suggest the task we just finished
        if suggestion and suggestion.id == task_id:
            suggestion = None

    return done, suggestion


# ──────────────────────────── drop ───────────────────────────────────


def drop_task(task_id: int, reason: Optional[str] = None) -> Tuple[Task, Optional[Task]]:
    """
    Mark task as DROPPED (no longer needed).
    Returns (dropped_task, suggested_next_task | None).
    Suggestion is only provided when the task was ACTIVE (freeing the slot).
    """
    task = db.fetch_task(task_id)
    if task is None:
        raise WSEError(f"Task #{task_id} not found.")
    if task.state == TaskState.DONE:
        raise WSEError(f"Task #{task_id} is already DONE — cannot drop it.")
    if task.state == TaskState.DROPPED:
        raise WSEError(f"Task #{task_id} is already DROPPED.")

    updates: dict = {"state": TaskState.DROPPED.value, "next_step": None}
    if reason:
        updates["block_reason"] = reason

    dropped = db.update_task(task_id, **updates)

    suggestion: Optional[Task] = None
    if task.state == TaskState.ACTIVE:
        suggestion = next_task()
        if suggestion and suggestion.id == task_id:
            suggestion = None

    return dropped, suggestion


# ──────────────────────────── block ──────────────────────────────────


def block_task(
    task_id: int,
    reason: str,
    follow_up_at: Optional[datetime] = None,
) -> Task:
    """Mark a task as BLOCKED with an optional follow-up reminder."""
    task = db.fetch_task(task_id)
    if task is None:
        raise WSEError(f"Task #{task_id} not found.")
    if task.state == TaskState.DONE:
        raise WSEError(f"Task #{task_id} is already DONE — cannot block it.")

    updates: dict = {
        "state": TaskState.BLOCKED.value,
        "block_reason": reason,
    }
    if follow_up_at:
        updates["follow_up_at"] = follow_up_at.isoformat(sep=" ", timespec="seconds")

    return db.update_task(task_id, **updates)


# ─────────────────────── follow-up check ─────────────────────────────


def check_followups() -> List[Task]:
    """Return tasks due for follow-up (caller handles notification)."""
    return db.fetch_due_followups()


def mark_task_alerted(task_id: int) -> None:
    db.mark_alerted(task_id)
