"""Tests for service.list_tasks."""

from __future__ import annotations

from task_engine import db, service
from task_engine.models import TaskState
from tests.conftest import make_task


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
