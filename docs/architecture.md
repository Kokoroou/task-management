# Architecture & Design

## ⚙️ **Overall Workflow**

```
[CLI Input]
   ↓
[main.py — Typer app + callback]
   ↓
[commands/ — lifecycle / query / update / system]
   ↓
[service.py — business rules & state machine]
   ↓
[db.py — SQLite access]
   ↓
[models.py — Task dataclass & TaskState enum]
```

Notifications are dispatched from `system.py` (check-followup command) via `alerts.py`.

---

## 🧩 **Components**

### ⚡ **1. CLI Interface**

Running `task` with no subcommand shows the next recommended task.

| Command | Description |
|---|---|
| `task` | Show the next task (shorthand for `task next`) |
| `task add` | Create a new TODO task |
| `task start` | Start a task (auto-interrupts the current one) |
| `task done` | Mark a task as DONE |
| `task drop` | Drop a task (no longer needed, stays in DB) |
| `task block` | Mark a task as BLOCKED with an optional follow-up |
| `task update` | Edit title, next_step, or block_reason without changing state |
| `task next` | Show the next recommended task |
| `task list` | List tasks (excludes DONE/DROPPED by default) |
| `task show` | Show full details of a task |
| `task check-followup` | Check and alert on overdue BLOCKED tasks (cron use) |
| `task delete` | Permanently delete a task from the database |

---

### 🗄️ **2. Storage (Single Source of Truth)**

- SQLite (local file at `~/.task_engine.db`)
- No external service dependency
- Zero setup, zero latency

---

### 🧠 **3. State Engine**

Handles:

- State transitions between task states
- Enforces rules (1 ACTIVE task at a time, mandatory `next_step` when interrupting)
- Manages parent-child task relationships

---

### 🎯 **4. Next Task Selector**

Priority order:

1. `ACTIVE` task (already running)
2. Most recently updated `INTERRUPTED` task
3. Oldest `TODO` task

`BLOCKED` tasks are **never** returned by `next_task()`.

👉 Always returns **exactly 1 task** (or nothing when the slate is clear)

---

### 🔔 **5. Follow-up Alert System**

- Runs in batches (every 30 minutes via cron)
- Only alerts on `BLOCKED` tasks whose `follow_up_at` is due and not yet alerted
- Batches multiple tasks into a single notification
- Silent (exit 0, no output) when nothing is due — cron-friendly

👉 No spam, no flow interruption

---

## 🧱 **Data Model**

A task contains:

| Field | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incremented primary key |
| `title` | TEXT | Task description |
| `state` | TEXT | One of: `TODO` / `ACTIVE` / `INTERRUPTED` / `BLOCKED` / `DONE` / `DROPPED` |
| `parent_id` | INTEGER? | FK to parent task (sub-task support) |
| `next_step` | TEXT? | Where to resume after an interruption |
| `block_reason` | TEXT? | Why the task is blocked (or drop reason) |
| `follow_up_at` | TEXT? | ISO datetime for follow-up reminder |
| `last_alerted_at` | TEXT? | Last time a follow-up notification was sent |
| `created_at` | TEXT | ISO datetime |
| `updated_at` | TEXT | ISO datetime, updated on every write |

---

## 🏗️ **Code Structure**

Strict 4-layer pipeline — **no circular dependencies, no layer skipping**:

```
models.py → db.py → service.py → main.py
                                      ↑
                  commands/ (lifecycle, query, update, system)
                  cli_utils.py (shared formatting helpers)
                  alerts.py (called from commands/system.py only)
```

```
task-management/
├── task_engine/
│   ├── __init__.py          # Package version metadata
│   ├── models.py            # Task dataclass & TaskState enum (pure data, no logic)
│   ├── db.py                # All SQLite access (CRUD + follow-up queries)
│   ├── service.py           # Business rules & state-machine (WSEError raised here)
│   ├── cli_utils.py         # Shared Rich formatting helpers, STATE_ICON/STATE_STYLE
│   ├── alerts.py            # Cross-platform desktop notifications
│   ├── main.py              # Typer app, callback (bare `task`), command registration
│   └── commands/
│       ├── __init__.py
│       ├── lifecycle.py     # add, start, done, drop
│       ├── query.py         # next, list, show
│       ├── update.py        # update, block
│       └── system.py        # init, check-followup, delete
├── docs/                    # Documentation
├── pyproject.toml           # Build config, dev extras (ruff, mypy, pytest)
└── README.md
```

---

## ⚖️ **Design Decisions**

### ✅ **CLI-first**
- Fast, low friction
- Cross-platform (Linux / Windows / WSL / macOS)

---

### ✅ **Local-first**
- No API
- No sync
- No latency

---

### ✅ **No AI (v1)**
- No auto planning
- No estimation

👉 Keeps the system deterministic and trustworthy

---

### ✅ **Minimalism**
- No dashboard
- No kanban board
- No complex UI

---

## ⚠️ **Non-goals (intentionally out of scope)**

- ❌ Not a replacement for Jira / Todoist
- ❌ No complex scheduling
- ❌ No time tracking
- ❌ No collaboration

👉 This is a personal tool focused on **execution**, not management.
