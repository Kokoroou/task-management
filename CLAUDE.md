# CLAUDE.md

Project instructions for Claude Code. Read this file at the start of every session to understand the project's working culture and technical standards.

## Project Overview

**Work State Engine (WSE)** — A CLI-first personal workflow tool for managing tasks through a strict state machine. Designed for developers who live in the terminal and want minimal friction when tracking what they are working on, what is blocked, and what comes next.

The core insight: at any moment you should have at most one ACTIVE task, and every interruption or block should leave a breadcrumb (`next_step` / `block_reason`) so context is never lost.

## Tech Stack

- **Python 3.10+**
- **Typer** — CLI framework (argument / option parsing, help generation)
- **Rich** — Terminal output formatting (colors, tables, icons)
- **SQLite** (stdlib `sqlite3`) — Single-file database at `~/.task_engine.db`
- **Platform notifications** — `notify-send` (Linux), `osascript` (macOS), `win10toast` / PowerShell (Windows)

No ORM. No async. No external database server. Dependencies are intentionally minimal.

## Workflows

```bash
# Install in editable mode (development)
pip install -e .

# Install with Windows toast notifications
pip install -e ".[windows]"

# Run via installed entry-point
task <command>

# Run without installing (useful in CI or quick tests)
python -m task_engine.main <command>
```

### Common CLI commands

```bash
task init                                       # Initialise the DB (safe to re-run)
task add "Task title" [--parent ID]             # Add a new TODO task
task start ID [--next-step "Where I left off"]  # Start a task; interrupts the current one
task done ID                                    # Mark a task DONE
task drop ID [--reason "why"]                   # Drop a task no longer needed
task block ID --reason "Waiting for..." [--follow-up "2025-03-20 09:00"]
task update ID --next-step "New next step"      # Update next step note without changing state
task update ID --block-reason "New reason"      # Update block reason without changing state
task update ID --next-step "" --block-reason "" # Clear both fields
task next                                       # Show the best task to work on next
task list [--all]                               # List tasks (--all includes DONE/DROPPED)
task show ID                                    # Show full details of a task
task check-followup                             # Check overdue blocked tasks (run from cron)
```

## Architecture

Strict 4-layer pipeline — no circular dependencies, no layer skipping:

```
models.py → db.py → service.py → main.py
                                     ↑
                               alerts.py (called from main.py only)
```

**`models.py`** — Pure data layer. `TaskState` enum (TODO / ACTIVE / INTERRUPTED / BLOCKED / DONE / DROPPED) and `Task` dataclass with `from_row()` for SQLite deserialization. No logic here.

**`db.py`** — All SQLite access. Every function opens and closes its own connection via the `get_conn()` context manager (WAL mode, foreign keys on). `update_task()` is a generic kwargs-based updater: only the keyword arguments explicitly passed are written to the database; passing `None` sets the column to NULL.

**`service.py`** — All business rules and state-machine constraints live here. Key invariants:
- Only one `ACTIVE` task at a time. `start_task()` raises `WSEError` if another task is active and no `next_step` is provided for the interruption.
- `start_task()` **preserves** `next_step` and `block_reason` on the newly activated task. These fields are historical context and are only cleared by explicit user action (`task update ID --next-step ""`).
- `next_task()` priority: ACTIVE → most-recently-updated INTERRUPTED → oldest TODO. BLOCKED tasks are never returned by `next_task()`.
- `done_task()` returns a suggestion: parent task (if sub-task and not yet done) or `next_task()` result.
- `update_task_fields()` edits `next_step` and `block_reason` in-place without changing state. Pass `""` to clear either field.

**`main.py`** — Typer CLI and Rich formatting only. No business logic. Every command calls `db.init_db()` first (idempotent), then delegates to `service`. `WSEError` exceptions are caught and printed; all other exceptions surface normally.

**`alerts.py`** — Notification dispatch only, called from `main.py`'s `check-followup` command. Platform detection: Linux → `notify-send`, macOS → `osascript`, Windows → `win10toast` or PowerShell fallback, fallback → stdout print.

## Coding Standards

- **Layer discipline**: never call `db.*` from `main.py`; never call `service.*` from `db.py`. The 4-layer order is absolute.
- **Error handling**: raise `WSEError` for domain-level user errors in `service.py`. Let it propagate to `main.py` where it is caught and printed without a traceback. All other exceptions are unexpected and should surface normally.
- **Field clearing convention**: `None` as a function argument means "do not touch this field". `""` (empty string) means "clear this field" — the service layer converts `""` to `None` before writing to the database.
- **No silent mutations**: every state change must go through `service.py`. `main.py` never writes to the database directly.
- **Idempotent init**: `db.init_db()` is called at the start of every CLI command so no prior `task init` is ever required.

## Key Behaviours to Preserve

- `start_task()` in `service.py` requires `next_step_for_current` when interrupting an active task — enforced at the service layer, not just the CLI prompt.
- `check-followup` is silent when there is nothing to do (no output, exit 0) — cron-friendly by design.
- `update_task()` in `db.py` only modifies the columns passed as kwargs; unmentioned columns are untouched.

## Testing

There is no test suite yet (v0.1.0 POC). There is no linter or formatter configured.

When tests are added, use **pytest**. Place test files under `tests/`. Mirror the module structure: `tests/test_service.py`, `tests/test_db.py`, etc. Use an in-memory SQLite database (`:memory:`) to keep tests isolated and fast.
