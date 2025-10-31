from typing import Optional

import click

from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID
from phable.utils import text_from_cli_arg_or_fs_or_editor


@click.command(name="comment")
@click.option(
    "--comment",
    type=str,
    help="Comment text or path to a text file containing the comment body. If not provided, an editor will be opened.",
)
@click.argument("task-id", type=TASK_ID)
@click.pass_obj
def comment_on_task(client: PhabricatorClient, task_id: int, comment: Optional[str]):
    """Add a comment to a task

    \b
    Example:
    $ phable comment T123456 --comment 'hello'              # set comment body from the cli itself
    $ phable comment T123456 --comment path/to/comment.txt  # set comment body from a text file
    $ phable comment T123456                                # set comment body from your own text editor

    """
    comment = text_from_cli_arg_or_fs_or_editor(comment)
    client.create_or_edit_task(task_id=task_id, params={"comment": comment})
