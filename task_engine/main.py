"""CLI interface for Work State Engine (WSE).

Usage:
    task init
    task add "Title of new task" [--parent ID]
    task start ID [--next-step "Where I left off..."]
    task done ID
    task drop ID [--reason "why"]
    task block ID --reason "Waiting for..." [--follow-up "2025-03-20 09:00"]
    task update ID --next-step "New next step"
    task next
    task list [--all]
    task show ID
    task check-followup
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from task_engine import db, service
from task_engine.alerts import notify_followups
from task_engine.models import Task, TaskState
from task_engine.service import WSEError

app = typer.Typer(
    name="task",
    help="Work State Engine — CLI-first personal workflow tool.",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)
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


# ─────────────────────────── commands ────────────────────────────────


@app.command()
def init():
    """Initialise the database (safe to run multiple times)."""
    db.init_db()
    rprint(f"[green]✔[/green] Database ready: [cyan]{db.get_db_path()}[/cyan]")


@app.command()
def add(
    title: str = typer.Argument(..., help="Task title"),
    parent: Optional[int] = typer.Option(None, "--parent", "-p", help="Parent task ID"),
):
    """Add a new task in TODO state."""
    db.init_db()
    try:
        task = service.add_task(title, parent_id=parent)
    except WSEError as e:
        _abort_on_error(e)
        return

    rprint(f"[green]✔ Added[/green] #{task.id}  {task.title}")


@app.command()
def start(
    task_id: int = typer.Argument(..., help="ID of the task to start"),
    next_step: Optional[str] = typer.Option(
        None,
        "--next-step", "-n",
        help="Where you left off on the CURRENT task (required when switching)",
    ),
):
    """Start working on a task (interrupts the current one if needed)."""
    db.init_db()

    # If there's an active task and no --next-step, prompt interactively
    current = service.get_active()
    if current and current.id != task_id and not next_step:
        rprint(
            f"[yellow]⏸  You are currently working on[/yellow] "
            f"[bold]#{current.id} \"{current.title}\"[/bold]"
        )
        next_step = typer.prompt("  Where did you leave off? (next step)")

    try:
        interrupted, active = service.start_task(task_id, next_step_for_current=next_step)
    except WSEError as e:
        _abort_on_error(e)
        return

    if interrupted:
        rprint(
            f"[yellow]⏸  Interrupted[/yellow] #{interrupted.id}  {interrupted.title}\n"
            f"     [italic cyan]→ next: {interrupted.next_step}[/italic cyan]"
        )
    rprint(f"[bold green]▶  Started[/bold green]  #{active.id}  {active.title}")


@app.command()
def done(
    task_id: int = typer.Argument(..., help="ID of the task to mark done"),
):
    """Mark a task as DONE."""
    db.init_db()
    try:
        finished, suggestion = service.done_task(task_id)
    except WSEError as e:
        _abort_on_error(e)
        return

    rprint(f"[bold green]✔  Done[/bold green]    #{finished.id}  {finished.title}")

    if suggestion:
        rprint("\n[bold]Next up:[/bold]")
        rprint(_fmt_task_line(suggestion))


@app.command()
def drop(
    task_id: int = typer.Argument(..., help="ID of the task to drop"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Why is this task being dropped?"),
):
    """Drop a task — mark it as no longer needed (stays in DB)."""
    db.init_db()

    task = db.fetch_task(task_id)
    if task is None:
        rprint(f"[bold red]Error:[/bold red] Task #{task_id} not found.")
        raise typer.Exit(code=1)

    # Require confirmation when dropping an ACTIVE task
    if task.state == TaskState.ACTIVE:
        rprint(f"[bold yellow]⚠  Task #{task.id} \"{task.title}\" is currently ACTIVE.[/bold yellow]")
        confirmed = typer.confirm("  Are you sure you want to drop it?", default=False)
        if not confirmed:
            rprint("[dim]Aborted.[/dim]")
            raise typer.Exit(code=0)
        if reason is None:
            raw = typer.prompt("  Reason for dropping (optional, press Enter to skip)", default="")
            reason = raw or None

    try:
        dropped, suggestion = service.drop_task(task_id, reason=reason)
    except WSEError as e:
        _abort_on_error(e)
        return

    rprint(f"[dim]⊘  Dropped[/dim]   #{dropped.id}  {dropped.title}")
    if dropped.block_reason:
        rprint(f"   [dim]Reason: {dropped.block_reason}[/dim]")

    if suggestion:
        rprint("\n[bold]Next up:[/bold]")
        rprint(_fmt_task_line(suggestion))


@app.command()
def block(
    task_id: int = typer.Argument(..., help="ID of the task to block"),
    reason: str = typer.Option(..., "--reason", "-r", help="Why is it blocked?"),
    follow_up: Optional[str] = typer.Option(
        None,
        "--follow-up", "-f",
        help="Reminder datetime, e.g. '2025-03-20 09:00'",
    ),
):
    """Mark a task as BLOCKED with an optional follow-up reminder."""
    db.init_db()

    follow_up_dt: Optional[datetime] = None
    if follow_up:
        try:
            follow_up_dt = datetime.fromisoformat(follow_up)
        except ValueError:
            rprint("[red]Error:[/red] Invalid datetime format. Use: YYYY-MM-DD HH:MM")
            raise typer.Exit(code=1)

    try:
        task = service.block_task(task_id, reason=reason, follow_up_at=follow_up_dt)
    except WSEError as e:
        _abort_on_error(e)
        return

    rprint(f"[bold red]✖  Blocked[/bold red]  #{task.id}  {task.title}")
    rprint(f"   Reason: {reason}")
    if follow_up_dt:
        rprint(f"   Follow-up: {follow_up_dt.strftime('%Y-%m-%d %H:%M')}")


@app.command(name="next")
def next_cmd():
    """Show the best task to work on next."""
    db.init_db()
    task = service.next_task()
    if task is None:
        rprint("[dim]No tasks pending — you're all clear! 🎉[/dim]")
        return
    rprint("[bold]Next task:[/bold]")
    rprint(_fmt_task_line(task))


@app.command(name="list")
def list_cmd(
    all_tasks: bool = typer.Option(False, "--all", "-a", help="Include DONE and DROPPED tasks"),
):
    """List all tasks."""
    db.init_db()
    tasks = service.list_tasks(all_tasks=all_tasks)
    if not tasks:
        rprint("[dim]No tasks found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("ID", style="dim", width=4)
    table.add_column("State", width=14)
    table.add_column("Title")
    table.add_column("Next Step / Reason", style="italic cyan")

    for t in tasks:
        state_style = STATE_STYLE[t.state]
        icon = STATE_ICON[t.state]
        extra = t.next_step or t.block_reason or ""
        table.add_row(
            str(t.id),
            f"[{state_style}]{icon} {t.state.value}[/{state_style}]",
            t.title + (f" [dim](↑#{t.parent_id})[/dim]" if t.parent_id else ""),
            extra,
        )

    console.print(table)


@app.command()
def show(
    task_id: int = typer.Argument(..., help="Task ID"),
):
    """Show full details of a task."""
    db.init_db()
    task = db.fetch_task(task_id)
    if task is None:
        rprint(f"[red]Task #{task_id} not found.[/red]")
        raise typer.Exit(code=1)

    rprint(_fmt_task_line(task))
    rprint(f"  Created:  {task.created_at}")
    rprint(f"  Updated:  {task.updated_at}")
    if task.follow_up_at:
        rprint(f"  Follow-up: {task.follow_up_at}")


@app.command(name="update")
def update_cmd(
    task_id: int = typer.Argument(..., help="Task ID"),
    next_step: Optional[str] = typer.Option(
        None,
        "--next-step", "-n",
        help="Update the 'next step' note (use '' to clear it)",
    ),
):
    """Update mutable fields of a task (e.g. next step) without changing state."""
    db.init_db()
    try:
        task = service.update_task_fields(task_id, next_step=next_step)
    except service.WSEError as e:
        _abort_on_error(e)
        return

    rprint(f"[green]✔ Updated[/green] #{task.id}  {task.title}")
    if task.next_step:
        rprint(f"     [italic cyan]→ next: {task.next_step}[/italic cyan]")
    else:
        rprint("     [italic dim]→ next step cleared[/italic dim]")


@app.command(name="check-followup")
def check_followup():
    """Check for overdue blocked tasks and send notifications (run from cron)."""
    db.init_db()
    tasks = service.check_followups()

    if not tasks:
        return  # silent — cron-friendly

    notify_followups(tasks)

    for t in tasks:
        service.mark_task_alerted(t.id)
        rprint(f"[yellow]⏰ Follow-up:[/yellow] #{t.id} {t.title}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
