from typing import Optional

import click

from phable.cli.utils import find_project_phid_by_title, project_phid_option
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
@click.option(
    "--status",
    "statuses",
    required=False,
    multiple=True,
    type=click.Choice(TaskStatus._member_names_, case_sensitive=False),
    help="The task status to filter on. Can be passed multiple times.",
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
    "--format",
    required=False,
    type=click.Choice(TaskFormat, case_sensitive=False),
    default="plain",
    help="The output format of the task list",
)
@click.pass_context
@click.pass_obj
def list_tasks(
    client: PhabricatorClient,
    ctx: click.Context,
    columns: list[str],
    project: Optional[str],
    owner: Optional[str] = None,
    statuses: tuple[str, ...] = (),
    milestone: bool = False,
    format: TaskFormat = TaskFormat.PLAIN,
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

    """
    if owner:
        if owner == "self":
            owner_user = client.current_user()["phid"]
        else:
            owner_data = client.find_user_by_username(owner)
            owner_user = owner_data["phid"] if owner_data else None
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
    tasks = client.find_tasks(
        column_phids=column_phids,
        owner_phid=owner_user,
        project_phid=project_phid,
        statuses=list(statuses),
    )
    if owner_user:
        tasks += client.find_tasks(
            column_phids=column_phids,
            backup_owner_phid=owner_user,
            project_phid=project_phid,
            statuses=list(statuses),
        )
    tasks = list({task["id"]: task for task in tasks}.values())
    tasks = [client.enrich_task(task) for task in tasks]
    display_tasks(tasks=tasks, format=format)
