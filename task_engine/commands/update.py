"""Update commands: update, block."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer
from rich import print as rprint

from task_engine import db, service
from task_engine.cli_utils import _abort_on_error
from task_engine.service import WSEError


def register(app: typer.Typer) -> None:
    @app.command(name="update")
    def update_cmd(
        task_id: int = typer.Argument(..., help="Task ID"),
        title: Optional[str] = typer.Option(
            None,
            "--title", "-t",
            help="Rename the task",
        ),
        next_step: Optional[str] = typer.Option(
            None,
            "--next-step", "-n",
            help="Update the 'next step' note (use '' to clear it)",
        ),
        block_reason: Optional[str] = typer.Option(
            None,
            "--block-reason", "-r",
            help="Update the block reason note (use '' to clear it)",
        ),
    ):
        """Update mutable fields of a task (title, next step, block reason) without changing state."""
        db.init_db()
        try:
            task = service.update_task_fields(task_id, title=title, next_step=next_step, block_reason=block_reason)
        except WSEError as e:
            _abort_on_error(e)
            return

        rprint(f"[green]✔ Updated[/green] #{task.id}  {task.title}")
        if title is not None:
            rprint(f"     [italic]Title → {task.title}[/italic]")
        if task.next_step:
            rprint(f"     [italic cyan]→ next: {task.next_step}[/italic cyan]")
        elif next_step is not None:
            rprint("     [italic dim]→ next step cleared[/italic dim]")
        if task.block_reason:
            rprint(f"     [italic red]✖ reason: {task.block_reason}[/italic red]")
        elif block_reason is not None:
            rprint("     [italic dim]✖ block reason cleared[/italic dim]")

    @app.command()
    def block(
        task_id: int = typer.Argument(..., help="ID of the task to block"),
        reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Why is it blocked?"),
        follow_up: Optional[str] = typer.Option(
            None,
            "--follow-up", "-f",
            help="Reminder datetime, e.g. '2025-03-20 09:00'",
        ),
    ):
        """Mark a task as BLOCKED with an optional follow-up reminder."""
        db.init_db()

        if not reason:
            task = db.fetch_task(task_id)
            if task is not None:
                rprint(f"[bold red]✖  Blocking[/bold red] #{task.id}  \"{task.title}\"")
            reason = typer.prompt("  Why is this task blocked?")

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
