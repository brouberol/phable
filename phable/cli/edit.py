import tempfile
from pathlib import Path

import click

from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID
from phable.utils import text_from_cli_arg_or_fs_or_editor


@click.command(name="edit")
@click.argument("task-id", type=TASK_ID, required=True)
@click.pass_context
@click.pass_obj
def edit_task(client: PhabricatorClient, ctx: click.Context, task_id: int):
    """Edit the description text of the argument task

    \b
    Example:
    $ phable edit T123456
    """
    task = client.show_task(task_id=task_id)
    initial_description_filepath = Path(
        tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", delete=False
        ).name
    )
    initial_description_filepath.write_text(task["fields"]["description"]["raw"])
    updated_description = text_from_cli_arg_or_fs_or_editor(
        path=initial_description_filepath, force_editor=True
    )
    client.edit_description(task_id=task_id, description=updated_description)
    initial_description_filepath.unlink(missing_ok=True)
