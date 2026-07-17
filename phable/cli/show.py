import click

from phable.cli.utils import choices_from_enum
from phable.display import TaskFormat, display_task
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID, Task


@click.command(name="show")
@click.option(
    "--format",
    type=choices_from_enum(TaskFormat),
    default=TaskFormat.plain,
    help="Output format",
)
@click.option("--full", "show_full", is_flag=True, help="Also show task comments")
@click.argument("task-id", type=TASK_ID, required=True)
@click.pass_obj
def show_task(
    client: PhabricatorClient,
    task_id: int,
    format: str = TaskFormat.plain,
    show_full: bool = False,
):
    """Show task details

    \b
    Examples:
    $ phable show T123456                 # show task details as plaintext
    $ phable show T123456 --full          # show task details with comments
    $ phable show T123456 --format=json   # show task details as json

    """
    if task := client.show_task(task_id):
        task = client.enrich_task(
            task,
            with_author_owner=True,
            with_tags=True,
            with_subtasks=True,
            with_parent=True,
            with_comments=show_full,
        )
        display_task(task=task, format=format)
    else:
        click.echo(f"Task {Task.from_int(task_id)} not found", err=True)
