import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID, TaskStatus


@click.command(name="status")
@click.option(
    "--status",
    type=click.Choice(TaskStatus._member_names_),
    help="Task(s) status",
    required=True,
)
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC)
@click.pass_obj
def set_task_status(client: PhabricatorClient, task_ids: list[int], status: TaskStatus):
    """Set the status of one or multiple tasks [DEPRECATED]

    \b
    Example:
    # Set the status for a single task
    $ phable status T123456 --status progress
    \b
    # Set the status for a multiple tasks
    $ phable status T123456 T123457 --status declined

    """
    click.secho(
        "[DEPRECATION NOTICE] This command has been replaced by `phable set --status`  and will soon be removed",
        fg="yellow",
    )
    for task_id in task_ids:
        client.set_task_status(task_id=task_id, status=status)
