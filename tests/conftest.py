"""Shared fixtures for the WSE test suite."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from task_engine import db
from task_engine.models import Task

# ---------------------------------------------------------------------------
# In-memory DB fixture — patches db.DB_PATH so every test gets a clean slate
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_db(tmp_path: Path):
    """
    Redirect db.DB_PATH to a fresh temporary file for each test.
    Using a file-based temp DB (not :memory:) because the db layer
    opens/closes connections per-call, which doesn't work with :memory:.
    """
    db_file = tmp_path / "test_wse.db"
    with patch.object(db, "DB_PATH", db_file):
        db.init_db()
        yield db_file


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_task(title: str = "Test task", parent_id: int | None = None) -> Task:
    """Insert a TODO task and return it."""
    return db.insert_task(title, parent_id=parent_id)
