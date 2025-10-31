import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID


@click.group()
def parent():
    """Manage task parents"""


@parent.command(name="set")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.option("--parent-ids", type=TASK_ID, help="ID(s) of parent task", multiple=True)
@click.pass_obj
def set_task_parent(
    client: PhabricatorClient,
    task_ids: list[int],
    parent_ids: list[int],
):
    """Set the parent task(s) of the argument task(s)

    \b
    Examples:
    \b
    # Set parent of a single task
    $ phable parent set T123456 --parent-ids T234567
    \b
    # Set parent of multiple tasks
    $ phable parent set T123456 T123457 --parent-ids T234567
    \b
    # Set multiple parents for a single task
    $ phable parent set T123456 --parent-ids T234567 T234568
    \b

    """
    parent_phids = []
    for parent_id in parent_ids:
        parent_task = client.show_task(task_id=parent_id)
        parent_phids.append(parent_task["phid"])

    for task_id in task_ids:
        client.edit_parent_tasks(task_id, parent_task_phids=parent_phids, action="set")


@parent.command(name="add")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.option("--parent-ids", type=TASK_ID, help="ID(s) of parent task", multiple=True)
@click.pass_obj
def add_task_parent(
    client: PhabricatorClient,
    task_ids: list[int],
    parent_ids: list[int],
):
    """Add the parent task(s) to the argument task(s) parents list

    \b
    Examples:
    \b
    # Add parent to a single task
    $ phable parent add T123456 --parent-ids T234567
    \b
    # Add parent to multiple tasks
    $ phable parent add T123456 T123457 --parent-ids T234567
    \b
    # Add multiple parents to a single task
    $ phable parent add T123456 --parent-ids T234567 T234568
    \b

    """
    parent_phids = []
    for parent_id in parent_ids:
        parent_task = client.show_task(task_id=parent_id)
        parent_phids.append(parent_task["phid"])

    for task_id in task_ids:
        client.edit_parent_tasks(task_id, parent_task_phids=parent_phids, action="add")


@parent.command(name="remove")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.option("--parent-ids", type=TASK_ID, help="ID(s) of parent task", multiple=True)
@click.pass_obj
def remove_task_parent(
    client: PhabricatorClient,
    task_ids: list[int],
    parent_ids: list[int],
):
    """Remove the parent task(s) from the argument task(s) parents list

    \b
    Examples:
    \b
    # Remove parent from a single task
    $ phable parent remove T123456 --parent-ids T234567
    \b
    # Remove parent from multiple tasks
    $ phable parent remove T123456 T123457 --parent-ids T234567
    \b
    # Remove multiple parents from a single task
    $ phable parent remove T123456 --parent-ids T234567 T234568
    \b

    """
    parent_phids = []
    for parent_id in parent_ids:
        parent_task = client.show_task(task_id=parent_id)
        parent_phids.append(parent_task["phid"])

    for task_id in task_ids:
        client.edit_parent_tasks(
            task_id, parent_task_phids=parent_phids, action="remove"
        )
