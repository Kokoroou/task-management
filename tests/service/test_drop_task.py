"""Tests for service.drop_task."""

from __future__ import annotations

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
