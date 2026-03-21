# Automation & Alerts

## 🔔 **Setting Up Cron / Scheduler (Follow-up Alerts)**

### Linux / WSL

Add to crontab (`crontab -e`):

```cron
*/30 * * * * /usr/local/bin/task check-followup
```

If using a virtual environment:

```cron
*/30 * * * * /path/to/venv/bin/task check-followup
```

Notifications use `notify-send`. Install it:

```bash
sudo apt install libnotify-bin
```

On WSL, also install `wslu` to enable native Windows notifications:

```bash
sudo apt install wslu
```

### macOS

Add to crontab (`crontab -e`):

```cron
*/30 * * * * /usr/local/bin/task check-followup
```

Notifications use `osascript` (built-in on macOS — no extra install needed).

### Windows (Task Scheduler)

1. Open **Task Scheduler** → Create Basic Task
2. Name: `WSE Follow-up Alert`
3. Trigger: Daily, repeat every **30 minutes**
4. Action: Start a program
   - Program: `task`
   - Arguments: `check-followup`
5. Finish

Notifications use PowerShell toast (built-in) or install win10toast for richer notifications:

```bash
pip install win10toast
# or during project install:
pip install -e ".[windows]"
```

---

## 🔕 **Behaviour**

- `task check-followup` is **silent** (no output, exit 0) when no tasks are due — safe for cron.
- When tasks are due, it sends a **batched desktop notification** (one notification for all overdue tasks) and prints each overdue task to stdout.
- After alerting, `last_alerted_at` is updated so the same task is not re-notified for the same follow-up time.
