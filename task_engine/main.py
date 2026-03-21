"""CLI interface for Work State Engine (WSE).

Usage:
    task add "Title of new task" [--parent ID]
    task start ID [--next-step "Where I left off..."]
    task done ID
    task drop ID [--reason "why"]
    task block ID --reason "Waiting for..." [--follow-up "2025-03-20 09:00"]
    task update ID --title "New title"
    task update ID --next-step "New next step"
    task update ID --block-reason "New block reason"
    task update ID --next-step "" --block-reason ""  # clear both
    task next
    task list [--all]
    task show ID
    task check-followup
"""

from __future__ import annotations

import typer
from rich import print as rprint

from task_engine import db, service
from task_engine.cli_utils import _fmt_task_line
from task_engine.commands import lifecycle, query, system, update

app = typer.Typer(
    name="task",
    help="Work State Engine — CLI-first personal workflow tool.",
    add_completion=False,
    pretty_exceptions_show_locals=False,
    invoke_without_command=True,
)


@app.callback()
def main_callback(ctx: typer.Context):
    """Work State Engine — run `task` to see what's next, or `task --help` for all commands."""
    if ctx.invoked_subcommand is None:
        db.init_db()
        t = service.next_task()
        if t is None:
            rprint("[dim]No tasks pending — you're all clear! 🎉[/dim]")
        else:
            rprint("[bold]Next task:[/bold]")
            rprint(_fmt_task_line(t))


# Register commands in workflow order:
# lifecycle → query → update → system
lifecycle.register(app)
query.register(app)
update.register(app)
system.register(app)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
