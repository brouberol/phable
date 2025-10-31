from typing import Optional

import click

from phable.cli.utils import VARIADIC
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID


@click.command(name="tag")
@click.option("--tag", type=str, help="Tag name")
@click.argument("task-ids", type=TASK_ID, nargs=VARIADIC)
@click.pass_obj
def tag_task(client: PhabricatorClient, task_ids: list[int], tag: Optional[str]):
    """Add a tag on one or multiple tasks

    \b
    Example:
    $ phable tag T123456 --tag 'Essential work'          # add a single tag to a task
    $ phable tag T123456 T123457 --tag 'Essential work'  # add multiple tags to a task

    """
    if tag := client.find_project_by_title(title=tag):
        for task_id in task_ids:
            client.assign_tag_to_task(task_id=task_id, tag_phid=tag["phid"])
    else:
        click.echo(f"Tag '{tag}' not found", err=True)
