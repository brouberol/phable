import click
from typing import Optional
from phable.config import config
from phable.cli.utils import VARIADIC, project_phid_option
from phable.phabricator import PhabricatorClient
from phable.utils import Task


@click.command(name="move")
@click.option(
    "--column",
    type=str,
    required=True,
    help="Name of destination column.",
)
@click.option(
    "--milestone/--no-milestone",
    default=False,
    help=(
        "If --milestone is passed, the task will be moved onto the current project's associated "
        "milestone board, instead of the project board itself"
    ),
)
@project_phid_option
@click.argument("task-ids", type=Task.from_str, nargs=VARIADIC, required=True)
@click.pass_context
@click.pass_obj
def move_task(
    client: PhabricatorClient,
    ctx: click.Context,
    project_phid: Optional[str],
    task_ids: list[int],
    column: Optional[str],
    milestone: bool,
) -> None:
    """Move one or several task on their current project board

    If the task is moved to a 'Done' column, it will be automatically
    marked as 'Resolved' as well.

    \b
    Example:
    $ phable move T123456 --column 'In Progress'
    $ phable move T123456 T234567 --column 'Done'
    $ phable move --project-phid PHID-PROJ-1234567890 --column 'Done' T123456

    """
    try:
        target_project_phid = client.get_main_project_or_milestone(
            milestone=milestone,
            project_phid=project_phid or config.phabricator_default_project_phid,
        )
        target_column_phid = client.find_column_in_project(target_project_phid, column)

        for task_id in task_ids:
            client.move_task_to_column(task_id=task_id, column_phid=target_column_phid)
            if column.lower() in ("in progress", "needs review"):
                client.mark_task_as_in_progress(task_id)
            if column.lower() == "done":
                client.mark_task_as_resolved(task_id)
    except ValueError as ve:
        ctx.fail(ve)
