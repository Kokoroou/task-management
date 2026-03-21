"""Tests for service.done_task."""

from __future__ import annotations

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
