"""Query commands: next, list, show."""

from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from task_engine import db, service
from task_engine.cli_utils import STATE_ICON, STATE_STYLE, _fmt_task_line, console


def register(app: typer.Typer) -> None:
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
