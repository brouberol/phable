from collections import defaultdict
from typing import Optional

import click

from phable.cli.utils import find_project_phid_by_title, project_phid_option
from phable.config import config
from phable.phabricator import PhabricatorClient


@click.command(name="move-project-tasks")
@project_phid_option
@click.option(
    "--from",
    "source",
    default=None,
    help="Name of the source milestone. Defaults to the previous milestone.",
)
@click.option(
    "--to",
    "target",
    default=None,
    help="Name of the target milestone. Defaults to the current active milestone.",
)
@click.option(
    "--ignore-column",
    "ignored_columns",
    multiple=True,
    default=("Reported",),
    show_default=True,
    help="Column name to exclude from the move. Can be repeated.",
)
@click.pass_context
@click.pass_obj
def move_project_tasks(
    client: PhabricatorClient,
    ctx: click.Context,
    project: Optional[str],
    source: Optional[str],
    target: Optional[str],
    ignored_columns: tuple[str, ...],
) -> None:
    """Move tasks from the previous milestone to the new one, preserving their column.

    By default, uses the two most recent milestones of the default project.
    Tasks in ignored columns (default: Reported) are not moved.

    \b
    Examples:
    # Auto-detect source and target milestones
    $ phable move-project-tasks
    \b
    # Specify both milestones explicitly
    $ phable move-project-tasks --from "2026-02-13 - 2026-03-06" --to "2026-03-06 - 2026-03-27"
    """
    try:
        project_phid = (
            find_project_phid_by_title(client, ctx, project)
            or config.phabricator_default_project_phid
        )

        milestones = client.find_milestones_for_project(project_phid)
        if len(milestones) < 2:
            ctx.fail("Need at least 2 milestones to perform rollover.")

        milestones_by_name = {m["fields"]["name"]: m for m in milestones}

        if source:
            if source not in milestones_by_name:
                ctx.fail(f"Milestone '{source}' not found.")
            source_milestone = milestones_by_name[source]
        else:
            source_milestone = milestones[-2]

        if target:
            if target not in milestones_by_name:
                ctx.fail(f"Milestone '{target}' not found.")
            target_milestone = milestones_by_name[target]
        else:
            target_milestone = milestones[-1]

        source_phid = source_milestone["phid"]
        target_phid = target_milestone["phid"]
        source_name = source_milestone["fields"]["name"]
        target_name = target_milestone["fields"]["name"]

        # Validate column mapping before touching any tasks
        column_map = client.validate_and_build_column_map(
            source_phid, target_phid, ignored_columns
        )

        # Build PHID → name map for display (columns are cached after validate)
        source_col_name = {
            col["phid"]: col["fields"]["name"]
            for col in client.list_project_columns(source_phid)
        }

        # Fetch tasks for preview
        tasks_with_columns = client.find_tasks_in_project_columns(source_phid, ignored_columns)

        if not tasks_with_columns:
            click.echo(f"No tasks to move from '{source_name}'.")
            return

        # Group by column for summary display
        by_column: dict = defaultdict(list)
        for task, col_phid in tasks_with_columns:
            by_column[col_phid].append(task)

        click.echo(f"\nMoving tasks from '{source_name}' → '{target_name}':")
        for col_phid, col_tasks in by_column.items():
            click.echo(f"  {source_col_name[col_phid]}: {len(col_tasks)} task(s)")
        click.echo(f"\n  Total: {len(tasks_with_columns)} task(s)")

        click.confirm("\nProceed?", abort=True)

        moved = client.move_tasks_to_milestone(source_phid, target_phid, ignored_columns)
        click.echo(f"\nMoved {len(moved)} task(s) to '{target_name}'.")

    except ValueError as e:
        ctx.fail(str(e))