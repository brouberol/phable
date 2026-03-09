from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID, TaskPriority


@click.command(name="set")
@click.option(
    "--priority", type=click.Choice(TaskPriority._member_names_), help="Task(s) priority"
)
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC)
@click.pass_obj
def set_task_fields(
    client: PhabricatorClient, task_ids: list[int], priority: Optional[str]
):
    """Set the fields of one or multiple tasks

    \b
    Example:
    # Set the priority for a single task
    $ phable set T123456 --priority high
    \b
    # Set the priority for multiple tasks
    $ phable set T123456 T123457 --priority medium

    """
    for task_id in task_ids:
        client.create_or_edit_task(task_id=task_id, params={'priority': priority})
