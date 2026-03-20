# Usage Guide

## 🚀 **Installation**

### Requirements

- Python 3.10+
- pip

### Install

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

## 🌐 **Global Command Setup**

To use the `task` command from anywhere, follow these steps:

### Windows (PowerShell)

1. Find the path to your Python Scripts folder (usually `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python3x\Scripts` or within your virtual environment's `Scripts` folder).
2. Add this path to your System Environment Variables:
   - Search for "Edit the system environment variables" in the Start menu.
   - Click **Environment Variables**.
   - Under **System variables**, find `Path` and click **Edit**.
   - Click **New** and paste the path to your `Scripts` folder.
   - Restart your terminal.

Alternatively, if you installed via `pip install .`, it should already be available if your Python Scripts folder is in your PATH.

### Ubuntu / Linux

1. Ensure your local bin directory is in your PATH. Add this to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
2. Reload your configuration:
   ```bash
   source ~/.bashrc
   ```
3. If you installed it in a virtual environment, you can create a symbolic link to `/usr/local/bin`:
   ```bash
   sudo ln -s /path/to/your/venv/bin/task /usr/local/bin/task
   ```

---

## ⚡ **Quick Start**

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

## 📋 **All Commands**

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
