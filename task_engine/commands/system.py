"""System commands: init, check-followup, delete."""

from __future__ import annotations

import typer
from rich import print as rprint

from task_engine import db, service
from task_engine.alerts import notify_followups
from task_engine.cli_utils import _abort_on_error
from task_engine.service import WSEError


def register(app: typer.Typer) -> None:
    @app.command(hidden=True)
    def init():
        """Initialise the database (safe to run multiple times)."""
        db.init_db()
        rprint(f"[green]✔[/green] Database ready: [cyan]{db.get_db_path()}[/cyan]")

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

    @app.command(name="delete")
    def delete_cmd(
        task_id: int = typer.Argument(..., help="ID of the task to permanently delete"),
    ):
        """Permanently delete a task from the database (cannot be undone)."""
        db.init_db()
        task = db.fetch_task(task_id)
        if task is None:
            rprint(f"[bold red]Error:[/bold red] Task #{task_id} not found.")
            raise typer.Exit(code=1)

        rprint(
            f"[bold red]⚠  This will permanently delete[/bold red] "
            f"#{task.id} \"{task.title}\" [dim]({task.state.value})[/dim]"
        )
        confirmed = typer.confirm("  Are you sure?", default=False)
        if not confirmed:
            rprint("[dim]Aborted.[/dim]")
            raise typer.Exit(code=0)

        try:
            service.delete_task(task_id)
        except WSEError as e:
            _abort_on_error(e)
            return

        rprint(f"[dim]🗑  Deleted[/dim]   #{task.id}  {task.title}")
