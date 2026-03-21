"""Tests for service.check_followups and service.mark_task_alerted."""

from __future__ import annotations

from datetime import datetime, timedelta

from task_engine import db, service
from task_engine.models import TaskState
from tests.conftest import make_task


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
