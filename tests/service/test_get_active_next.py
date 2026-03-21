"""Tests for service.get_active and service.next_task."""

from __future__ import annotations

import sqlite3

from task_engine import db, service
from task_engine.models import TaskState
from tests.conftest import make_task


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
