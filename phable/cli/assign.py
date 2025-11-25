from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID


@click.command(name="assign")
@click.option(
    "--username",
    required=False,
    help="The username to assign the task to. Self-assign the task if not provided.",
)
@click.option(
    "--secondary",
    is_flag=True,
    default=False,
    help="Assign the user as a secondary owner",
)
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC, required=True)
@click.pass_context
@click.pass_obj
def assign_task(
    client: PhabricatorClient,
    ctx: click.Context,
    task_ids: list[int],
    username: Optional[str],
    secondary: bool = False,
):
    """Assign one or multiple task ids to a username

    \b
    Examples:
    \b
    # self assign task
    $ phable assign T123456
    \b
    # assign to username
    $ phable assign T123456  --usernamme brouberol
    \b
    # assign to a secondary owner
    $ phable assign T123456  --usernamme brouberol --secondary

    """
    if not username:
        user = client.current_user()
    else:
        user = client.find_user_by_username(username)
        if not user:
            ctx.fail(f"User {username} was not found")
    for task_id in task_ids:
        client.assign_task_to_user(
            task_id=task_id, user_phid=user["phid"], secondary=secondary
        )
