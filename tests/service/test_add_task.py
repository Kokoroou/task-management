"""Tests for service.add_task."""

from __future__ import annotations

import pytest

from task_engine import service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
