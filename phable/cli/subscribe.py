import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID


@click.command(name="subscribe")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.pass_context
@click.pass_obj
def subscribe_to_task(
    client: PhabricatorClient, ctx: click.Context, task_ids: list[int]
):
    """Subscribe to one or multiple task ids

    \b
    Examples:
    $ phable subscribe T123456
    $ phable subscribe T123456 T234567

    """
    if user := client.current_user():
        for task_id in task_ids:
            client.add_user_to_task_subscribers(task_id=task_id, user_phid=user["phid"])
    else:
        ctx.fail("Current user was not found")
