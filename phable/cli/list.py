from typing import Optional
from datetime import datetime, UTC, timedelta
import click
from phable.cli.utils import (
    choices_from_enum,
    find_project_phid_by_title,
    project_phid_option,
    UPDATED_SINCE,
)
from phable.config import config
from phable.display import TaskFormat, display_tasks
from phable.phabricator import PhabricatorClient
from phable.task import TaskStatus


@click.command(name="list")
@click.option(
    "--column",
    "columns",
    required=False,
    help="The columns the tasks should be located in",
    multiple=True,
)
@click.option(
    "--owner",
    required=False,
    help="The username the tasks should be assigned to",
)
@project_phid_option
@click.option(
    "--milestone/--no-milestone",
    default=False,
    help=(
        "If --milestone is passed, the task will be moved onto the current project's associated "
        "milestone board, instead of the project board itself"
    ),
)
@click.option(
    "--status",
    required=False,
    type=choices_from_enum(TaskStatus),
    help="Task(s) status to filter on. Can be passed multiple times.",
    default=[TaskStatus.open, TaskStatus.progress, TaskStatus.stalled],
    multiple=True,
)
@click.option(
    "--format",
    required=False,
    type=choices_from_enum(TaskFormat),
    default=TaskFormat.oneline,
    help="The output format of the task list",
)
@click.option(
    "--updated-since",
    "updated_since_days",
    required=False,
    type=UPDATED_SINCE,
    help="Only return tasks edited since the provided duration",
)
@click.pass_context
@click.pass_obj
def list_tasks(
    client: PhabricatorClient,
    ctx: click.Context,
    columns: tuple[str],
    project: Optional[str],
    owner: Optional[str] = None,
    milestone: bool = False,
    status: tuple[str] | None = None,
    format: TaskFormat = TaskFormat.oneline,
    updated_since_days: int | None = None,
):
    """Lists and filter tasks

    \b
    Examples:
    # List all tasks in the default board
    $ phable list
    \b
    # List all open tasks in the default board latest milestone
    $ phable list --milestone --status open
    \b
    # List all tasks owner by brouberol in the Done column of the default board latest milestone
    $ phable list --milestone --owner brouberol --column Done
    \b
    # List all tasks owner by the current user in the Done column of the default board latest milestone
    $ phable list --milestone --owner self --column Done
    \b
    # List all tasks owner by the current user in the Done column of the default board latest milestone
    # updated in the last week
    $ phable list --milestone --owner self --column Done --updated-since 1w

    """
    if not any((columns, owner, milestone)):
        click.echo(
            click.style(
                "None of the --columns, --owner or --milestone flags were passed. "
                "The task search will be extremely wide, as it will return all open tasks. ",
                fg="yellow",
            ),
            err=True,
        )
        if not click.confirm("Continue?"):
            ctx.exit()

    if owner:
        owner_user = None
        if owner == "self":
            owner_user = client.current_user()["phid"]
        elif owner_user_data := client.find_user_by_username(owner):
            owner_user = owner_user_data["phid"]
        if not owner_user:
            ctx.fail(f"User {owner} was not found")
    else:
        owner_user = None

    project_phid = client.get_main_project_or_milestone(
        milestone=milestone,
        project_phid=find_project_phid_by_title(client, ctx, project)
        or config.phabricator_default_project_phid,
    )
    if columns:
        column_phids = [
            client.find_column_in_project(project_phid=project_phid, column_name=column)
            for column in columns
        ]
    else:
        column_phids = []

    updated_since = None
    if updated_since_days:
        updated_since = int(
            (datetime.now(UTC) - timedelta(days=updated_since_days)).timestamp()
        )
    tasks = client.find_tasks(
        column_phids=column_phids,
        owner_phid=owner_user,
        project_phid=project_phid,
        status=list(status) if status else None,
        updated_since=updated_since,
    )
    if owner_user:
        tasks += client.find_tasks(
            column_phids=column_phids,
            backup_owner_phid=owner_user,
            project_phid=project_phid,
            status=list(status) if status else None,
            updated_since=updated_since,
        )
    tasks = [client.enrich_task(task) for task in tasks]
    display_tasks(tasks=tasks, format=format)
