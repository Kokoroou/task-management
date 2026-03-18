"""Cross-platform push notifications for Work State Engine.

Supports:
- Linux: notify-send (libnotify)
- Windows: win10toast (optional) or PowerShell fallback
- Fallback: print to terminal
"""

from __future__ import annotations

import platform
import subprocess
from typing import List

from task_engine.models import Task


def _send_linux(title: str, message: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "--app-name", "WSE", title, message],
            check=False,
            timeout=5,
        )
    except FileNotFoundError:
        # notify-send not available — fall back to terminal
        _send_terminal(title, message)


def _send_windows(title: str, message: str) -> None:
    # Try win10toast first
    try:
        from win10toast import ToastNotifier  # type: ignore

        notifier = ToastNotifier()
        notifier.show_toast(
            title,
            message,
            duration=8,
            threaded=True,
        )
        return
    except ImportError:
        pass

    # Fallback: PowerShell balloon notification
    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        "$n.Visible = $true; "
        f'$n.ShowBalloonTip(8000, "{title}", "{message}", '
        "[System.Windows.Forms.ToolTipIcon]::Info); "
        "Start-Sleep -Seconds 9; "
        "$n.Dispose()"
    )
    try:
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            check=False,
            timeout=15,
        )
    except FileNotFoundError:
        _send_terminal(title, message)


def _send_terminal(title: str, message: str) -> None:
    """Ultimate fallback — print to stdout."""
    print(f"\n[WSE ALERT] {title}\n  {message}\n")


def send_notification(title: str, message: str) -> None:
    """Send a desktop notification using the best available method."""
    system = platform.system()
    if system == "Linux":
        _send_linux(title, message)
    elif system == "Windows":
        _send_windows(title, message)
    else:
        # macOS or unknown
        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                check=False,
                timeout=5,
            )
        except FileNotFoundError:
            _send_terminal(title, message)


def notify_followups(tasks: List[Task]) -> None:
    """Send a single batch notification for all overdue blocked tasks."""
    if not tasks:
        return

    if len(tasks) == 1:
        t = tasks[0]
        send_notification(
            "WSE — Follow-up reminder",
            f'#{t.id} "{t.title}" — {t.block_reason or "check this task"}',
        )
    else:
        lines = [f'#{t.id} "{t.title}"' for t in tasks]
        send_notification(
            f"WSE — {len(tasks)} tasks need follow-up",
            "\n".join(lines),
        )
