# Core Concepts

## 🎯 **Project Goal**

WSE is not a todo app.

It solves 3 real problems:

- ❌ Forgetting to follow up when waiting on someone else
- ❌ Getting interrupted and losing track of what you were doing
- ❌ Coming back to a task with no idea where to start

👉 Instead of managing a "list of things to do", WSE manages **task state**.

---

## 🧠 **Core Concept**

### 🔥 **State-based workflow**

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

## 🧠 **Mental Model**

> You don't need to know:  
> - how many tasks you have  

> You only need to know:  
> ✅ What you're working on right now  
> ✅ The exact next step  
> ✅ When to come back to something waiting  

---

## 📌 **Core Philosophy**

> ❗ Not optimising for "planning"  
> ✅ Optimising for "continuing to make progress"  

---

## 👤 **Target User**

- Dev / DevOps / knowledge worker
- Juggling multiple tasks in parallel
- Frequently interrupted
- No need for fancy UI — speed and efficiency first

---

## 🏁 **Summary**

WSE doesn't help you do more things.

It helps you:  
- **Never forget what matters**
- **Not waste time reloading context**
- **Always know what to do next**

→ So you work with **less stress, more focus, and more consistency**.
