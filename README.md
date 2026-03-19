# 🧠 Work State Engine (WSE)

> A **CLI-first personal workflow system** that always tells you:
> ✅ *"What should I work on next?"*
> ✅ *"When do I need to follow up on something waiting?"*
> ✅ *"How do I resume without losing context?"*

---

# 🎯 **Project Goal**

WSE is not a todo app.

It solves 3 real problems:

- ❌ Forgetting to follow up when waiting on someone else
- ❌ Getting interrupted and losing track of what you were doing
- ❌ Coming back to a task with no idea where to start

👉 Instead of managing a "list of things to do", WSE manages **task state**.

---

# 🧠 **Core Concept**

## 🔥 **State-based workflow**

Each task is not just text — it has a **clearly defined state**:

- `TODO` → not started
- `ACTIVE` → currently being worked on (only 1 at a time)
- `INTERRUPTED` → paused mid-way
- `BLOCKED` → waiting on an external dependency
- `DONE` → completed
- `DROPPED` → no longer needed (archived, not deleted)

---

## ✅ **Core Rules**

### 1. **Only 1 ACTIVE task at a time**
→ reduces decision fatigue

---

### 2. **Interruptions must save context**
→ when switching tasks:  
- the current task → `INTERRUPTED`
- `next_step` is mandatory before switching

---

### 3. **Resume without re-thinking**
→ every task carries:  
```
next_step = "the exact next action"  
```

---

### 4. **Side tasks must not kill the main task**
- Side task → has a `parent_id`
- Main task → goes `BLOCKED` while waiting

---

### 5. **Auto-resume parent**
→ when a child task is DONE:  
- the system automatically suggests resuming the parent task

---

### 6. **Follow-ups are never forgotten**
→ a `BLOCKED` task can have:  
```
follow_up_at  
```
→ the system will remind you at the right time

---

# ⚙️ **Overall Workflow**

```
[CLI Input]  
   ↓  
[SQLite DB]  
   ↓  
[State Engine]  
   ↓  
[Next Task Selector]  
   ↓  
[CLI Output / Notification]  
```

---

# 🧩 **Components**

## ⚡ **1. CLI Interface**
- `task init` → initialise the database
- `task add` → create a task
- `task start` → start working on a task
- `task done` → mark a task complete
- `task drop` → drop a task (no longer needed)
- `task block` → mark a task as blocked
- `task next` → get the next recommended task
- `task list` → list all tasks
- `task show` → view details of a task
- `task check-followup` → check for due follow-ups (for cron)

---

## 🗄️ **2. Storage (Single Source of Truth)**

- SQLite (local file)
- No external service dependency
- Zero setup, zero latency

---

## 🧠 **3. State Engine**

Handles:

- State transitions between task states
- Enforces rules (1 ACTIVE task, mandatory `next_step` on interrupt)
- Manages parent-child relationships

---

## 🎯 **4. Next Task Selector**

Priority order:

1. `ACTIVE` task (already running)
2. Most recently updated `INTERRUPTED` task
3. Oldest `TODO` task

👉 Always returns **exactly 1 task**

---

## 🔔 **5. Follow-up Alert System**

- Runs in batches (every 30 minutes via cron)
- Only alerts on `BLOCKED` tasks that are due
- Batches multiple tasks into a single notification

👉 No spam, no flow interruption

---

# 🧱 **Data Model**

A task contains:

- `id`
- `title`
- `state`
- `parent_id`
- `next_step`
- `block_reason`
- `follow_up_at`
- `last_alerted_at`
- `created_at`
- `updated_at`

---

# 🔄 **Key Flows**

## ✅ **Interrupt flow**

```
Task A (ACTIVE)  
   ↓ (Task B appears)  
Task A → INTERRUPTED + next_step saved  
Task B → ACTIVE  
```

---

## ✅ **Side task flow**

```
Task A (main)  
   ↓ needs env setup  
Task A → BLOCKED

Task B (side) → ACTIVE

Task B DONE  
   → system suggests resuming Task A  
```

---

## ✅ **Resume flow**

```
task next  
→ returns most recently updated INTERRUPTED task  
→ shows saved next_step  
```

---

## ✅ **Follow-up flow**

```
Task BLOCKED + follow_up_at set

→ time is reached  
→ system sends alert notification  
→ task surfaces in candidate list  
```

---

# ⚖️ **Design Decisions**

## ✅ **CLI-first**
- Fast, low friction
- Cross-platform (Linux / Windows / WSL / macOS)

---

## ✅ **Local-first**
- No API
- No sync
- No latency

---

## ✅ **No AI (v1)**
- No auto planning
- No estimation

👉 Keeps the system deterministic and trustworthy

---

## ✅ **Minimalism**
- No dashboard
- No kanban board
- No complex UI

---

# ⚠️ **Non-goals (intentionally out of scope)**

- ❌ Not a replacement for Jira / Todoist
- ❌ No complex scheduling
- ❌ No time tracking
- ❌ No collaboration

👉 This is a personal tool focused on **execution**, not management.

---

# 🧠 **Mental Model**

> You don't need to know:
> - how many tasks you have

> You only need to know:
> ✅ What you're working on right now
> ✅ The exact next step
> ✅ When to come back to something waiting

---

# 🚀 **Roadmap (post-POC)**

## Phase 1 (current)
- CLI
- State machine
- Follow-up alerts

---

## Phase 2 (UX)
- Global hotkey input
- Faster task capture

---

## Phase 3 (Visibility)
- Minimal overlay / tmux status bar

---

## Phase 4 (Intelligence — optional)
- Smarter next task suggestions
- Lightweight pattern recognition (no heavy AI)

---

# ✅ **Success Criteria**

The system is working if:

- You use it consistently for **3–5 days**
- You no longer experience:
  - forgotten tasks
  - lost context when resuming
  - drifting away from your main task

---

# 💣 **Failure Modes**

- Input too slow → you stop using it
- Skipping `next_step` → can't resume properly
- Alert spam → you start ignoring everything
- Over-engineering → project abandoned

---

# 📌 **Core Philosophy**

> ❗ Not optimising for "planning"
> ✅ Optimising for "continuing to make progress"

---

# 👤 **Target User**

- Dev / DevOps / knowledge worker
- Juggling multiple tasks in parallel
- Frequently interrupted
- No need for fancy UI — speed and efficiency first

---

# 🏁 **Summary**

WSE doesn't help you do more things.

It helps you:  
- **Never forget what matters**
- **Not waste time reloading context**
- **Always know what to do next**

→ So you work with **less stress, more focus, and more consistency**.

---

# 🚀 **Installation**

## Requirements

- Python 3.9+
- pip

## Install

```bash
# Clone the repo
git clone <repo-url>  
cd task-management

# Install in editable mode (for development)
pip install -e .

# Or install normally
pip install .  
```

Windows — install toast notifications (optional):

```bash
pip install "work-state-engine[windows]"  
```

---

# ⚡ **Quick Start**

```bash
# Initialise the database (first time only)
task init

# Add tasks
task add "Code feature A"  
task add "Fix urgent bug"

# Start task 1
task start 1

# Get interrupted by a bug → must fill in next_step
task start 2  
# ▶ WSE prompts: "Where did you leave off?"
# → type: "Writing function parse_config, stopped at line 42"

# Finish the bug fix
task done 2  
# ✔ Suggests resuming task 1 (interrupted with saved context)

# See what to work on next
task next

# List all tasks
task list

# Block a task waiting on someone
task block 1 --reason "Waiting for team review" --follow-up "2025-03-20 09:00"  
```

---

# 📋 **All Commands**

| Command | Description |
|---|---|
| `task init` | Initialise the database |
| `task add "title"` | Add a new task |
| `task add "title" --parent ID` | Add a sub-task |
| `task start ID` | Start a task (auto-interrupts the current one) |
| `task start ID --next-step "..."` | Start a task and pre-fill next_step for the current one |
| `task done ID` | Mark a task as done |
| `task drop ID` | Drop a task (no longer needed) |
| `task drop ID --reason "..."` | Drop a task with a reason |
| `task block ID --reason "..."` | Mark a task as blocked |
| `task block ID --reason "..." --follow-up "YYYY-MM-DD HH:MM"` | Block a task and set a follow-up reminder |
| `task next` | Show the next recommended task |
| `task list` | List active tasks (excludes DONE and DROPPED) |
| `task list --all` | List all tasks including DONE and DROPPED |
| `task show ID` | Show full details of a task |
| `task check-followup` | Check and send alerts for due follow-ups (cron use) |

---

# 🔔 **Setting Up Cron / Scheduler (Follow-up Alerts)**

## Linux / WSL

Add to crontab (`crontab -e`):

```cron
*/30 * * * * /usr/local/bin/task check-followup
```

If using a virtual environment:

```cron
*/30 * * * * /path/to/venv/bin/task check-followup
```

Notifications use `notify-send`. On WSL, install `wslu`:

```bash
sudo apt install libnotify-bin wslu  
```

## Windows (Task Scheduler)

1. Open **Task Scheduler** → Create Basic Task
2. Name: `WSE Follow-up Alert`
3. Trigger: Daily, repeat every **30 minutes**
4. Action: Start a program
   - Program: `task`
   - Arguments: `check-followup`
5. Finish

Notifications use PowerShell toast (built-in) or install:

```bash
pip install win10toast  
```

---

# 🗂️ **Project Structure**

```
task-management/  
├── task_engine/  
│   ├── __init__.py     # Package metadata  
│   ├── models.py       # Data models (Task, TaskState)  
│   ├── db.py           # SQLite layer  
│   ├── service.py      # Business logic / state machine  
│   ├── main.py         # Typer CLI commands  
│   └── alerts.py       # Cross-platform notifications  
├── pyproject.toml      # Package config & entry points  
└── README.md  
```

Database: `~/.task_engine.db` (SQLite, local file)
