"""Tests for service.update_task_fields."""

from __future__ import annotations

import pytest

from task_engine import db, service
from task_engine.models import TaskState
from task_engine.service import WSEError
from tests.conftest import make_task


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
