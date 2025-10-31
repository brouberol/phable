import click

from phable.display import TaskFormat, display_task
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID


@click.command(name="show")
@click.option(
    "--format",
    type=click.Choice(TaskFormat, case_sensitive=False),
    default="plain",
    help="Output format",
)
@click.argument("task-id", type=TASK_ID, required=True)
@click.pass_obj
def show_task(client: PhabricatorClient, task_id: int, format: str = "plain"):
    """Show task details

    \b
    Examples:
    $ phable show T123456                 # show task details as plaintext
    $ phable show T123456  --format=json  # show task details as json

    """
    if task := client.show_task(task_id):
        task = client.enrich_task(
            task,
            with_author_owner=True,
            with_tags=True,
            with_subtasks=True,
            with_parent=True,
        )
        display_task(task=task, format=format)
    else:
        click.echo(f"Task {Task.from_int(task_id)} not found", err=True)
