# Roadmap & Evolution

## 🚀 **Roadmap (post-POC)**

### Phase 1 — CLI Core ✅ (current)
- State machine (TODO / ACTIVE / INTERRUPTED / BLOCKED / DONE / DROPPED)
- Full command set: add, start, done, drop, block, update, delete, next, list, show, check-followup
- Follow-up alerts (cron-based, cross-platform)
- Sub-task support (parent-child relationships)

---

### Phase 2 — UX
- Global hotkey input
- Faster task capture

---

### Phase 3 — Visibility
- Minimal overlay / tmux status bar integration

---

### Phase 4 — Intelligence (optional)
- Smarter next-task suggestions
- Lightweight pattern recognition (no heavy AI)

---

## ✅ **Success Criteria**

The system is working if:

- You use it consistently for **3–5 days**
- You no longer experience:
  - forgotten follow-ups
  - lost context when resuming an interrupted task
  - drifting away from your main task

---

## 💣 **Failure Modes**

- Input too slow → you stop using it
- Skipping `next_step` → can't resume properly
- Alert spam → you start ignoring everything
- Over-engineering → project abandoned
