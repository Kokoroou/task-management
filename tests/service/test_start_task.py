"""Tests for service.start_task."""

from __future__ import annotations

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
