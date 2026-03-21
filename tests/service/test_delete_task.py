"""Tests for service.delete_task."""

from __future__ import annotations

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


class TestDeleteTask:
    def test_deletes_todo_task(self, mem_db):
        task = make_task("to be deleted")
        deleted = service.delete_task(task.id)
        assert deleted.id == task.id
        assert deleted.title == "to be deleted"
        # Task no longer exists in DB
        assert db.fetch_task(task.id) is None

    def test_deletes_active_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.ACTIVE.value)
        service.delete_task(task.id)
        assert db.fetch_task(task.id) is None

    def test_deletes_done_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DONE.value)
        service.delete_task(task.id)
        assert db.fetch_task(task.id) is None

    def test_deletes_dropped_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.DROPPED.value)
        service.delete_task(task.id)
        assert db.fetch_task(task.id) is None

    def test_deletes_blocked_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.BLOCKED.value, block_reason="waiting")
        service.delete_task(task.id)
        assert db.fetch_task(task.id) is None

    def test_deletes_interrupted_task(self, mem_db):
        task = make_task()
        db.update_task(task.id, state=TaskState.INTERRUPTED.value)
        service.delete_task(task.id)
        assert db.fetch_task(task.id) is None

    def test_raises_when_not_found(self, mem_db):
        with pytest.raises(WSEError, match="not found"):
            service.delete_task(999)

    def test_returns_snapshot_of_deleted_task(self, mem_db):
        task = make_task("snapshot test")
        db.update_task(task.id, next_step="resume here", state=TaskState.INTERRUPTED.value)
        snapshot = service.delete_task(task.id)
        # Snapshot reflects the state before deletion
        assert snapshot.title == "snapshot test"
        assert snapshot.state == TaskState.INTERRUPTED
        assert snapshot.next_step == "resume here"

    def test_cascade_sets_child_parent_id_to_null(self, mem_db):
        parent = make_task("parent")
        child = make_task("child", parent_id=parent.id)
        assert child.parent_id == parent.id

        service.delete_task(parent.id)

        # Child still exists
        child_after = db.fetch_task(child.id)
        assert child_after is not None
        assert child_after.title == "child"
        # parent_id is now NULL due to ON DELETE SET NULL
        assert child_after.parent_id is None

    def test_only_deletes_target_task(self, mem_db):
        t1 = make_task("keep me")
        t2 = make_task("delete me")
        service.delete_task(t2.id)
        assert db.fetch_task(t1.id) is not None
