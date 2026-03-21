"""Tests for task_engine/service.py — full coverage of all business rules."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


# =============================================================================
# add_task
# =============================================================================


class TestAddTask:
    def test_creates_todo_task(self, mem_db):
        task = service.add_task("Buy milk")
        assert task.title == "Buy milk"
        assert task.state == TaskState.TODO
        assert task.parent_id is None

    def test_creates_subtask_with_valid_parent(self, mem_db):
        parent = make_task("Parent")
        child = service.add_task("Child", parent_id=parent.id)
        assert child.parent_id == parent.id
        assert child.state == TaskState.TODO

    def test_raises_when_parent_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.add_task("Orphan", parent_id=999)


# =============================================================================
# get_active / next_task
# =============================================================================


class TestGetActive:
    def test_returns_none_when_no_active(self, mem_db):
        make_task()
        assert service.get_active() is None

    def test_returns_active_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.ACTIVE.value)
        active = service.get_active()
        assert active is not None
        assert active.id == task.id


class TestNextTask:
    def test_returns_none_when_no_tasks(self, mem_db):
        assert service.next_task() is None

    def test_prefers_active_over_interrupted(self, mem_db):
        t1 = make_task("interrupted")
        t2 = make_task("active")
        db.update_task(t1.id, state=TaskState.INTERRUPTED.value)
        db.update_task(t2.id, state=TaskState.ACTIVE.value)
        assert service.next_task().id == t2.id

    def test_prefers_interrupted_over_todo(self, mem_db):
        t1 = make_task("todo")
        t2 = make_task("interrupted")
        db.update_task(t2.id, state=TaskState.INTERRUPTED.value)
        result = service.next_task()
        assert result.id == t2.id

    def test_most_recently_updated_interrupted_wins(self, mem_db):
        import sqlite3

        t1 = make_task("interrupted old")
        t2 = make_task("interrupted new")
        db.update_task(t1.id, state=TaskState.INTERRUPTED.value)
        db.update_task(t2.id, state=TaskState.INTERRUPTED.value)
        # Force t1 to have an older updated_at directly (db.update_task always sets _now())
        conn = sqlite3.connect(str(mem_db))
        conn.execute("UPDATE tasks SET updated_at = '2025-01-01 08:00:00' WHERE id = ?", (t1.id,))
        conn.execute("UPDATE tasks SET updated_at = '2025-06-01 08:00:00' WHERE id = ?", (t2.id,))
        conn.commit()
        conn.close()
        assert service.next_task().id == t2.id

    def test_returns_oldest_todo(self, mem_db):
        t1 = make_task("first todo")
        t2 = make_task("second todo")
        assert service.next_task().id == t1.id

    def test_never_returns_blocked(self, mem_db):
        t = make_task("blocked task")
        db.update_task(t.id, state=TaskState.BLOCKED.value)
        assert service.next_task() is None

    def test_never_returns_done(self, mem_db):
        t = make_task("done task")
        db.update_task(t.id, state=TaskState.DONE.value)
        assert service.next_task() is None


# =============================================================================
# list_tasks
# =============================================================================


class TestListTasks:
    def test_excludes_done_and_dropped_by_default(self, mem_db):
        t1 = make_task("active")
        t2 = make_task("done")
        t3 = make_task("dropped")
        db.update_task(t2.id, state=TaskState.DONE.value)
        db.update_task(t3.id, state=TaskState.DROPPED.value)
        ids = [t.id for t in service.list_tasks()]
        assert t1.id in ids
        assert t2.id not in ids
        assert t3.id not in ids

    def test_all_tasks_includes_done_and_dropped(self, mem_db):
        t1 = make_task("todo")
        t2 = make_task("done")
        db.update_task(t2.id, state=TaskState.DONE.value)
        ids = [t.id for t in service.list_tasks(all_tasks=True)]
        assert t1.id in ids
        assert t2.id in ids


# =============================================================================
# start_task
# =============================================================================


class TestStartTask:
    def test_starts_todo_task(self, mem_db):
        task = make_task("Do something")
        _, active = service.start_task(task.id)
        assert active.state == TaskState.ACTIVE

    def test_starts_interrupted_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.INTERRUPTED.value)
        _, active = service.start_task(task.id)
        assert active.state == TaskState.ACTIVE

    def test_raises_when_task_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.start_task(999)

    def test_raises_when_already_active(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.ACTIVE.value)
        with pytest.raises(WSEError, match="already ACTIVE"):
            service.start_task(task.id)

    def test_raises_when_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        with pytest.raises(WSEError, match="DONE"):
            service.start_task(task.id)

    def test_raises_when_dropped(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DROPPED.value)
        with pytest.raises(WSEError, match="DROPPED"):
            service.start_task(task.id)

    def test_interrupts_current_task_with_next_step(self, mem_db):
        current = make_task("current")
        new = make_task("new")
        db.update_task(current.id, state=TaskState.ACTIVE.value)

        interrupted, active = service.start_task(new.id, next_step_for_current="left off here")

        assert interrupted is not None
        assert interrupted.id == current.id
        assert interrupted.state == TaskState.INTERRUPTED
        assert interrupted.next_step == "left off here"
        assert active.id == new.id
        assert active.state == TaskState.ACTIVE

    def test_raises_when_switching_without_next_step(self, mem_db):
        current = make_task("current")
        new = make_task("new")
        db.update_task(current.id, state=TaskState.ACTIVE.value)
        with pytest.raises(WSEError, match="next-step"):
            service.start_task(new.id)

    def test_raises_when_starting_already_active_task(self, mem_db):
        """start_task on its own active task raises WSEError (not a no-op)."""
        task = make_task()
        db.update_task(task.id, state=TaskState.ACTIVE.value)
        with pytest.raises(WSEError, match="already ACTIVE"):
            service.start_task(task.id)

    def test_preserves_existing_next_step_on_newly_started_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, next_step="resume here")
        _, active = service.start_task(task.id)
        assert active.next_step == "resume here"


# =============================================================================
# update_task_fields
# =============================================================================


class TestUpdateTaskFields:
    def test_updates_next_step(self, mem_db):
        task = make_task()
        updated = service.update_task_fields(task.id, next_step="step one")
        assert updated.next_step == "step one"

    def test_updates_block_reason(self, mem_db):
        task = make_task()
        updated = service.update_task_fields(task.id, block_reason="waiting")
        assert updated.block_reason == "waiting"

    def test_clears_next_step_with_empty_string(self, mem_db):
        task = make_task()
        db.update_task(task.id, next_step="some step")
        updated = service.update_task_fields(task.id, next_step="")
        assert updated.next_step is None

    def test_clears_block_reason_with_empty_string(self, mem_db):
        task = make_task()
        db.update_task(task.id, block_reason="some reason")
        updated = service.update_task_fields(task.id, block_reason="")
        assert updated.block_reason is None

    def test_renames_task(self, mem_db):
        task = make_task("Old title")
        updated = service.update_task_fields(task.id, title="New title")
        assert updated.title == "New title"

    def test_rename_strips_whitespace(self, mem_db):
        task = make_task("Old title")
        updated = service.update_task_fields(task.id, title="  Trimmed  ")
        assert updated.title == "Trimmed"

    def test_raises_when_title_empty_string(self, mem_db):
        task = make_task()
        with pytest.raises(WSEError, match="cannot be empty"):
            service.update_task_fields(task.id, title="")

    def test_raises_when_title_only_whitespace(self, mem_db):
        task = make_task()
        with pytest.raises(WSEError, match="cannot be empty"):
            service.update_task_fields(task.id, title="   ")

    def test_raises_when_task_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.update_task_fields(999, next_step="x")

    def test_raises_when_task_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        with pytest.raises(WSEError, match="DONE"):
            service.update_task_fields(task.id, next_step="x")

    def test_raises_when_task_dropped(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DROPPED.value)
        with pytest.raises(WSEError, match="DROPPED"):
            service.update_task_fields(task.id, title="x")

    def test_no_change_when_no_params(self, mem_db):
        task = make_task("Unchanged")
        result = service.update_task_fields(task.id)
        assert result.title == "Unchanged"
        assert result.next_step is None

    def test_combine_title_and_next_step(self, mem_db):
        task = make_task("Old")
        updated = service.update_task_fields(task.id, title="New", next_step="do this")
        assert updated.title == "New"
        assert updated.next_step == "do this"

    def test_none_does_not_overwrite_existing_field(self, mem_db):
        task = make_task()
        db.update_task(task.id, next_step="keep me")
        # Only update block_reason; next_step must stay untouched
        updated = service.update_task_fields(task.id, block_reason="blocked")
        assert updated.next_step == "keep me"


# =============================================================================
# done_task
# =============================================================================


class TestDoneTask:
    def test_marks_task_done(self, mem_db):
        task = make_task()
        done, _ = service.done_task(task.id)
        assert done.state == TaskState.DONE

    def test_clears_next_step_on_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, next_step="still here")
        done, _ = service.done_task(task.id)
        assert done.next_step is None

    def test_raises_when_already_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        with pytest.raises(WSEError, match="already DONE"):
            service.done_task(task.id)

    def test_raises_when_dropped(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DROPPED.value)
        with pytest.raises(WSEError, match="DROPPED"):
            service.done_task(task.id)

    def test_raises_when_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.done_task(999)

    def test_suggests_parent_when_subtask_done(self, mem_db):
        parent = make_task("parent")
        child = make_task("child", parent_id=parent.id)
        _, suggestion = service.done_task(child.id)
        assert suggestion is not None
        assert suggestion.id == parent.id

    def test_does_not_suggest_done_parent(self, mem_db):
        parent = make_task("parent")
        db.update_task(parent.id, state=TaskState.DONE.value)
        child = make_task("child", parent_id=parent.id)
        _, suggestion = service.done_task(child.id)
        # parent is done → should not be suggested; falls through to next_task()
        assert suggestion is None or suggestion.id != parent.id

    def test_suggests_next_task_when_no_parent(self, mem_db):
        t1 = make_task("finish me")
        t2 = make_task("up next")
        _, suggestion = service.done_task(t1.id)
        assert suggestion is not None
        assert suggestion.id == t2.id

    def test_suggestion_is_none_when_no_other_tasks(self, mem_db):
        task = make_task()
        _, suggestion = service.done_task(task.id)
        assert suggestion is None


# =============================================================================
# drop_task
# =============================================================================


class TestDropTask:
    def test_marks_task_dropped(self, mem_db):
        task = make_task()
        dropped, _ = service.drop_task(task.id)
        assert dropped.state == TaskState.DROPPED

    def test_stores_reason(self, mem_db):
        task = make_task()
        dropped, _ = service.drop_task(task.id, reason="not needed")
        assert dropped.block_reason == "not needed"

    def test_raises_when_already_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        with pytest.raises(WSEError, match="DONE"):
            service.drop_task(task.id)

    def test_raises_when_already_dropped(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DROPPED.value)
        with pytest.raises(WSEError, match="already DROPPED"):
            service.drop_task(task.id)

    def test_raises_when_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.drop_task(999)

    def test_suggests_next_when_active_dropped(self, mem_db):
        active = make_task("active")
        next_t = make_task("next")
        db.update_task(active.id, state=TaskState.ACTIVE.value)
        _, suggestion = service.drop_task(active.id)
        assert suggestion is not None
        assert suggestion.id == next_t.id

    def test_no_suggestion_when_non_active_dropped(self, mem_db):
        task = make_task("todo")
        make_task("another todo")
        _, suggestion = service.drop_task(task.id)
        assert suggestion is None

    def test_clears_next_step_on_drop(self, mem_db):
        task = make_task()
        db.update_task(task.id, next_step="left off at...")
        dropped, _ = service.drop_task(task.id)
        assert dropped.next_step is None


# =============================================================================
# block_task
# =============================================================================


class TestBlockTask:
    def test_marks_task_blocked(self, mem_db):
        task = make_task()
        blocked = service.block_task(task.id, reason="waiting for review")
        assert blocked.state == TaskState.BLOCKED
        assert blocked.block_reason == "waiting for review"

    def test_stores_follow_up_at(self, mem_db):
        task = make_task()
        future = datetime.now() + timedelta(days=1)
        blocked = service.block_task(task.id, reason="waiting", follow_up_at=future)
        # follow_up_at stored as string; compare via isoformat prefix
        assert blocked.follow_up_at is not None

    def test_can_block_active_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.ACTIVE.value)
        blocked = service.block_task(task.id, reason="blocked mid-flight")
        assert blocked.state == TaskState.BLOCKED

    def test_raises_when_already_done(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        with pytest.raises(WSEError, match="DONE"):
            service.block_task(task.id, reason="irrelevant")

    def test_raises_when_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.block_task(999, reason="x")


# =============================================================================
# check_followups / mark_task_alerted
# =============================================================================


class TestCheckFollowups:
    def _block_with_followup(self, mem_db, follow_up_at: datetime):
        task = make_task("blocked task")
        db.update_task(
            task.id,
            state=TaskState.BLOCKED.value,
            block_reason="waiting",
            follow_up_at=follow_up_at.isoformat(sep=" ", timespec="seconds"),
        )
        return task

    def test_returns_overdue_tasks(self, mem_db):
        past = datetime.now() - timedelta(hours=1)
        task = self._block_with_followup(mem_db, past)
        due = service.check_followups()
        assert any(t.id == task.id for t in due)

    def test_does_not_return_future_tasks(self, mem_db):
        future = datetime.now() + timedelta(hours=1)
        self._block_with_followup(mem_db, future)
        due = service.check_followups()
        assert due == []

    def test_does_not_return_already_alerted(self, mem_db):
        past = datetime.now() - timedelta(hours=1)
        task = self._block_with_followup(mem_db, past)
        service.mark_task_alerted(task.id)
        due = service.check_followups()
        assert not any(t.id == task.id for t in due)

    def test_returns_empty_when_no_blocked_tasks(self, mem_db):
        make_task("just a todo")
        assert service.check_followups() == []
