"""Shared CLI helpers — formatting, styling, error handling.

This module is imported by all commands/ submodules to avoid circular imports
with main.py.
"""

from __future__ import annotations

import typer
from rich import print as rprint
from rich.console import Console

from task_engine.models import Task, TaskState
from task_engine.service import WSEError

console = Console()

# ─────────────────── state color mapping ────────────────────────────

STATE_STYLE: dict[TaskState, str] = {
    TaskState.TODO: "white",
    TaskState.ACTIVE: "bold green",
    TaskState.INTERRUPTED: "bold yellow",
    TaskState.BLOCKED: "bold red",
    TaskState.DONE: "dim",
    TaskState.DROPPED: "dim",
}

STATE_ICON: dict[TaskState, str] = {
    TaskState.TODO: "○",
    TaskState.ACTIVE: "▶",
    TaskState.INTERRUPTED: "⏸",
    TaskState.BLOCKED: "✖",
    TaskState.DONE: "✔",
    TaskState.DROPPED: "⊘",
}


def _fmt_task_line(t: Task) -> str:
    icon = STATE_ICON[t.state]
    style = STATE_STYLE[t.state]
    line = f"[{style}]{icon} #{t.id}  {t.title}[/{style}]"
    if t.next_step:
        line += f"\n     [italic cyan]→ next: {t.next_step}[/italic cyan]"
    if t.block_reason:
        line += f"\n     [italic red]✖ reason: {t.block_reason}[/italic red]"
    if t.parent_id:
        line += f"  [dim](child of #{t.parent_id})[/dim]"
    return line


def _abort_on_error(exc: WSEError) -> None:
    rprint(f"[bold red]Error:[/bold red] {exc}")
    raise typer.Exit(code=1)
