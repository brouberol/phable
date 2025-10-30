from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.utils import TASK_ID


@click.command(name="assign")
@click.option(
    "--username",
    required=False,
    help="The username to assign the task to. Self-assign the task if not provided.",
)
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.pass_context
@click.pass_obj
def assign_task(
    client: PhabricatorClient,
    ctx: click.Context,
    task_ids: list[int],
    username: Optional[str],
):
    """Assign one or multiple task ids to a username

    \b
    Examples:
    \b
    # self assign task
    $ phable assign T123456
    \b
    # asign to username
    $ phable assign T123456  --usernamme brouberol

    """
    if not username:
        user = client.current_user()
    else:
        user = client.find_user_by_username(username)
        if not user:
            ctx.fail(f"User {username} was not found")
    for task_id in task_ids:
        client.assign_task_to_user(task_id=task_id, user_phid=user["phid"])
