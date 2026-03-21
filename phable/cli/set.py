from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID, TaskPriority, TaskStatus


@click.command(name="set")
@click.option(
    "--priority",
    type=click.Choice(TaskPriority._member_names_),
    help="Task(s) priority",
)
@click.option(
    "--status", type=click.Choice(TaskStatus._member_names_), help="Task(s) status"
)
@click.option("--tags", type=str, multiple=True, help="Task(s) tag(s)")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC)
@click.pass_context
@click.pass_obj
def set_task_fields(
    client: PhabricatorClient,
    ctx: click.Context,
    task_ids: list[int],
    priority: Optional[str],
    status: Optional[str],
    tags: list[str],
):
    """Set the fields of one or multiple tasks

    \b
    Example:
    # Set the priority for a single task
    $ phable set T123456 --priority high
    \b
    # Set the priority for multiple tasks
    $ phable set T123456 T123457 --priority medium
    \b
    # Set the status for a single task
    $ phable set T123456 --status resolved
    \b
    # Set the tags for a single task
    $ phable set T123456 --tags 'Epic' 'OKR'

    """
    tag_phids = []
    for tag in tags:
        if tag_meta := client.find_project_by_title(title=tag):
            tag_phids.append(tag_meta["phid"])
        else:
            ctx.fail(f"Tag '{tag}' not found")

    params: dict[str, str] = {}
    if priority:
        params["priority"] = priority
    if status:
        params["status"] = status
    for task_id in task_ids:
        client.create_or_edit_task(task_id=task_id, params=params)
