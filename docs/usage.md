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
pip install -e ".[windows]"
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
# Just run `task` to see what to work on next (no subcommand needed)
task

# Add tasks
task add "Code feature A"
task add "Fix urgent bug"

# Start task 1
task start 1

# Get interrupted by a bug → WSE prompts for next_step if not provided
task start 2
# ⏸  You are currently working on #1 "Code feature A"
#   Where did you leave off? (next step): Writing parse_config(), stopped at line 42

# Or pass next_step inline to skip the prompt
task start 2 --next-step "Writing parse_config(), stopped at line 42"

# Finish the bug fix → suggests resuming task 1
task done 2

# See what to work on next
task next

# List all active tasks
task list

# List everything including DONE/DROPPED
task list --all

# Block a task waiting on someone
task block 1 --reason "Waiting for team review" --follow-up "2026-03-25 09:00"

# Block without a reason → WSE prompts interactively
task block 1

# Update task title or notes without changing state
task update 1 --title "New title"
task update 1 --next-step "Refactored config parser, need to add tests"
task update 1 --next-step "" --block-reason ""   # clear both fields

# Drop a task no longer needed (stays in DB)
task drop 3 --reason "Requirement removed"

# Permanently delete a task (cannot be undone — asks for confirmation)
task delete 3
```

---

## 📋 **All Commands**

| Command | Description |
|---|---|
| `task` | Show the next recommended task (same as `task next`) |
| `task add "title"` | Add a new TODO task |
| `task add "title" --parent ID` | Add a sub-task |
| `task start ID` | Start a task (auto-interrupts the current one) |
| `task start ID --next-step "..."` | Start a task and pre-fill the next_step for the current one |
| `task done ID` | Mark a task as DONE |
| `task drop ID` | Drop a task — mark as no longer needed (stays in DB) |
| `task drop ID --reason "..."` | Drop a task with a reason |
| `task block ID` | Mark a task as BLOCKED (prompts for reason) |
| `task block ID --reason "..."` | Mark a task as BLOCKED with a reason |
| `task block ID --reason "..." --follow-up "YYYY-MM-DD HH:MM"` | Block with a follow-up reminder |
| `task update ID --title "..."` | Rename a task |
| `task update ID --next-step "..."` | Update the next_step note |
| `task update ID --block-reason "..."` | Update the block_reason note |
| `task update ID --next-step "" --block-reason ""` | Clear both notes |
| `task next` | Show the next recommended task |
| `task list` | List active tasks (excludes DONE and DROPPED) |
| `task list --all` | List all tasks including DONE and DROPPED |
| `task show ID` | Show full details of a task |
| `task check-followup` | Check and send alerts for due follow-ups (cron use) |
| `task delete ID` | Permanently delete a task from the database |
