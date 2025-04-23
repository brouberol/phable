import click
from typing import Optional

from phable.phabricator import PhabricatorClient
from phable.config import config
from phable.display import display_tasks


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
    type=click.Choice(("html", "plain", "json", "markdown")),
    default="plain",
    help="The output format of the task list",
)
@click.pass_context
@click.pass_obj
def list_tasks(
    client: PhabricatorClient,
    ctx: click.Context,
    columns: list[str],
    owner: Optional[str] = None,
    milestone: bool = False,
    format: str = "plain",
):
    """Lists and filter tasks

    \b
    Examples:
    # List all tasks in the default board
    $ phable list
    \b
    # List all tasks in the default board latest milestone
    $ phable list --milestone
    \b
    # List all tasks owner by brouberol in the Done column of the default board latest milestone
    $ phable list --milestone --owner brouberol --column Done

    """
    if owner:
        owner_user = client.find_user_by_username(owner)["phid"]
        if not owner_user:
            ctx.fail(f"User {owner} was not found")
    else:
        owner_user = None
    project_phid = client.get_main_project_or_milestone(
        project_phid=config.phabricator_default_project_phid, milestone=milestone
    )
    if columns:
        column_phids = [
            client.find_column_in_project(project_phid=project_phid, column_name=column)
            for column in columns
        ]
    else:
        column_phids = None
    tasks = client.find_tasks(
        column_phids=column_phids, owner_phid=owner_user, project_phid=project_phid
    )
    tasks = [client.enrich_task(task) for task in tasks]
    display_tasks(tasks=tasks, format=format, separator="")
