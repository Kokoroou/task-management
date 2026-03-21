"""Tests for service.block_task."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
