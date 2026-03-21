"""Lifecycle commands: add, start, done, drop."""

from __future__ import annotations

from typing import Optional

import typer
from rich import print as rprint

from task_engine import db, service
from task_engine.cli_utils import _abort_on_error, _fmt_task_line
from task_engine.models import TaskState
from task_engine.service import WSEError


def register(app: typer.Typer) -> None:
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
