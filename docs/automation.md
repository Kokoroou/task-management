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

Notifications use `notify-send`. On WSL, install `wslu`:

```bash
sudo apt install libnotify-bin wslu  
```

### Windows (Task Scheduler)

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
