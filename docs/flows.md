# Key Flows

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
