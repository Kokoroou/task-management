# Architecture & Design

## ⚙️ **Overall Workflow**

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

## 🧩 **Components**

### ⚡ **1. CLI Interface**
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

### 🗄️ **2. Storage (Single Source of Truth)**

- SQLite (local file)
- No external service dependency
- Zero setup, zero latency

---

### 🧠 **3. State Engine**

Handles:

- State transitions between task states
- Enforces rules (1 ACTIVE task, mandatory `next_step` on interrupt)
- Manages parent-child relationships

---

### 🎯 **4. Next Task Selector**

Priority order:

1. `ACTIVE` task (already running)
2. Most recently updated `INTERRUPTED` task
3. Oldest `TODO` task

👉 Always returns **exactly 1 task**

---

### 🔔 **5. Follow-up Alert System**

- Runs in batches (every 30 minutes via cron)
- Only alerts on `BLOCKED` tasks that are due
- Batches multiple tasks into a single notification

👉 No spam, no flow interruption

---

## 🧱 **Data Model**

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

## 🗂️ **Project Structure**

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

---

## ⚠️ **Non-goals (intentionally out of scope)**

- ❌ Not a replacement for Jira / Todoist
- ❌ No complex scheduling
- ❌ No time tracking
- ❌ No collaboration

👉 This is a personal tool focused on **execution**, not management.
