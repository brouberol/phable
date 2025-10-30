from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.utils import Task


@click.command(name="parent")
@click.option("--parent-id", type=Task.from_str, help="ID of parent task")
@click.argument("task-ids", type=Task.from_str, nargs=VARIADIC, required=True)
@click.pass_context
@click.pass_obj
def change_task_parent(
    client: PhabricatorClient,
    ctx: click.Context,
    task_ids: list[int],
    parent_id: Optional[str],
):
    """Set the parent task of the argument tasks

    \b
    Examples:
    \b
    # Change parent of a single task
    $ phable parent T123456 --parent-id T234567
    \b
    # Change parent of multiple tasks
    $ phable assign T123456 T123457 --parent-id T234567

    """
    parent_task = client.show_task(task_id=parent_id)
    for task_id in task_ids:
        client.set_parent_task_id(task_id, parent_task_phid=parent_task["phid"])
