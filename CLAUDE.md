# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable mode for development)
pip install -e .

# Install with Windows toast notifications
pip install -e ".[windows]"

# Run the CLI
task <command>

# Run a single command manually (without install)
python -m task_engine.main <command>

task drop ID [--reason "why"]  # Drop a task no longer needed
```

There is no test suite yet (v0.1.0 POC). There is no linter or formatter configured.

## Architecture

The codebase is a strict 4-layer pipeline with no circular dependencies:

```
models.py → db.py → service.py → main.py
                                     ↑
                               alerts.py (called from main.py only)
```

**`models.py`** — Pure data. `TaskState` enum (TODO/ACTIVE/INTERRUPTED/BLOCKED/DONE/DROPPED) and `Task` dataclass with `from_row()` for SQLite deserialization.

**`db.py`** — All SQLite access. Single file at `~/.task_engine.db`. Every function opens and closes its own connection via `get_conn()` context manager (WAL mode, foreign keys on). `update_task()` is a generic kwargs-based updater used by the service layer.

**`service.py`** — All business rules live here. Key constraints enforced:
- Only one `ACTIVE` task at a time — `start_task()` raises `WSEError` if no `next_step` is provided when interrupting
- `next_task()` priority: ACTIVE → most-recently-updated INTERRUPTED → oldest TODO (BLOCKED tasks are never returned by `next_task()`)
- `done_task()` returns a suggestion: parent task (if sub-task) or next_task() result

**`main.py`** — Typer CLI, Rich formatting only. No business logic. Each command calls `db.init_db()` first (idempotent), then delegates to `service`. Errors from `WSEError` are caught and printed; all other exceptions surface normally.

**`alerts.py`** — Notification dispatch only. Called from `main.py` `check-followup` command. Platform detection: Linux → `notify-send`, Windows → `win10toast` or PowerShell fallback, macOS → `osascript`, fallback → stdout print.

## Key behaviours to preserve

- `start_task()` in `service.py` requires `next_step_for_current` when there is an active task being interrupted — this is intentional and enforced at the service layer, not just the CLI.
- `check-followup` is designed to be silent when there's nothing to do (no output, exit 0) — cron-friendly.
- `db.init_db()` is called at the start of every CLI command, making every command safe to run without a prior `task init`.
