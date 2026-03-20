# 🧠 Work State Engine (WSE)

> A **CLI-first personal workflow system** that always tells you:  
> ✅ *"What should I work on next?"*  
> ✅ *"When do I need to follow up on something waiting?"*  
> ✅ *"How do I resume without losing context?"*  

---

## 📑 Table of Contents

1. [Concepts & Philosophy](docs/concepts.md) - Project goals, core rules, and mental model.
2. [Architecture & Design](docs/architecture.md) - Technical overview, components, and data model.
3. [User Guide & Installation](docs/usage.md) - How to install, setup global commands, and quick start.
4. [Key Flows](docs/flows.md) - Visualizing how tasks move through the system.
5. [Automation & Alerts](docs/automation.md) - Setting up follow-up reminders (Cron/Task Scheduler).
6. [Roadmap & Criteria](docs/roadmap.md) - Future plans and success/failure metrics.

---

## ⚡ Quick Start (Preview)

```bash
# Initialise
task init

# Add and start
task add "My first task"
task start 1
```

For full instructions, see the [Usage Guide](docs/usage.md).

---

## 🛠️ Project Structure

```
task-management/  
├── task_engine/        # Core logic
├── docs/               # Documentation
├── pyproject.toml      # Configuration
└── README.md           # Entry point
```

---

## 👤 Target User

- Dev / DevOps / knowledge worker
- Juggling multiple tasks in parallel
- Frequently interrupted

---

## 🏁 Summary

WSE helps you **never forget what matters** and **always know what to do next**.
Check out the [Core Concepts](docs/concepts.md) to learn more.
