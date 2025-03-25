import os
import json

import click

from .phabricator import PhabricatorClient
from .utils import text_from_cli_arg_or_fs_or_editor


@click.group()
def cli():
    """Phabricator Maniphest CLI"""
    pass


class Task(int):
    @classmethod
    def from_str(cls, value: str) -> int:
        return int(value.lstrip("T"))

    @classmethod
    def from_int(cls, value: int) -> str:
        return f"T{value}"


@cli.command(name="show")
@click.option(
    "--format",
    type=click.Choice(("plain", "json")),
    default="plain",
    help="Output format",
)
@click.argument("task-id", type=Task.from_str)
def show_task(task_id: int, format: str = "plain"):
    """Show information about a Phabricator task"""
    client = PhabricatorClient()
    if task := client.show_task(task_id):
        author = client.show_user(phid=task["fields"]["authorPHID"])
        if owner_id := task["fields"]["ownerPHID"]:
            owner = client.show_user(phid=owner_id)["fields"]["username"]
        else:
            owner = "Unassigned"
        if project_ids := task["attachments"]["projects"]["projectPHIDs"]:
            tags = [
                (
                    f"{project['fields']['parent']['name']} - {project['fields']['name']}"
                    if project["fields"]["parent"]
                    else project["fields"]["name"]
                )
                for project in client.show_projects(phids=project_ids)
            ]
        else:
            tags = []
        subtasks = client.find_subtasks(parent_id=task_id)
        task["subtasks"] = subtasks
        parent = client.find_parent_task(subtask_id=task_id)
        task["parent"] = parent
        if format == "json":
            click.echo(json.dumps(task))
        else:
            parent_str = (
                f"{Task.from_int(parent['id'])} - {parent['fields']['name']}"
                if parent
                else ""
            )
            click.echo(f"URL: {client.base_url}/{Task.from_int(task_id)}")
            click.echo(f"Task: {Task.from_int(task_id)}")
            click.echo(f"Title: {task['fields']['name']}")
            click.echo(f"Author: {author['fields']['username']}")
            click.echo(f"Owner: {owner}")
            click.echo(f"Tags: {', '.join(tags)}")
            click.echo(f"Status: {task['fields']['status']['name']}")
            click.echo(f"Priority: {task['fields']['priority']['name']}")
            click.echo(f"Description: {task['fields']['description']['raw']}")
            click.echo(f"Parent: {parent_str}")
            click.echo("Subtasks:")
            if subtasks:
                for subtask in subtasks:
                    status = f"{'[x]' if subtask['fields']['status']['value'] == 'resolved' else '[ ]'}"
                    if subtask_owner_id := subtask["fields"]["ownerPHID"]:
                        owner = client.show_user(subtask_owner_id)["fields"]["username"]
                    else:
                        owner = ""
                    click.echo(
                        f"{status} - {Task.from_int(subtask['id'])} - @{owner:<10} - {subtask['fields']['name']}"
                    )
    else:
        click.echo(f"Task {Task.from_int(task_id)} not found")


@cli.command(name="create")
@click.option("--title", required=True, help="Title of the task")
@click.option(
    "--description",
    help="Task description or path to a file containing the description body. If not provided, an editor will be opened.",
)
@click.option(
    "--priority",
    type=click.Choice(["unbreaknow", "high", "normal", "low", "needs-triage"]),
    help="Priority level of the task",
    default="normal",
)
@click.option("--parent-id", type=int, help="ID of parent task")
@click.pass_context
def create_task(
    ctx,
    title: str,
    description: str,
    priority: str,
    parent_id: str | None,
):
    """Create a new Maniphest task"""
    client = PhabricatorClient()
    description = text_from_cli_arg_or_fs_or_editor(description)
    task_params = {
        "title": title,
        "description": description,
        "projects.add": [os.environ["PHABRICATOR_DEFAULT_PROJECT_PHID"]],
        "priority": priority,
    }
    if parent_id:
        parent = client.show_task(parent_id)
        task_params["parents.add"] = [parent["phid"]]

    task = client.create_or_edit_task(task_params)
    ctx.invoke(show_task, task_id=task["result"]["object"]["id"])


@cli.command(name="assign")
@click.option(
    "--username",
    required=False,
    help="The username to assign the task to. Self-assign the task if not provided.",
)
@click.argument("task-ids", type=Task.from_str, nargs=-1)
@click.pass_context
def assign_task(ctx, task_ids: list[int], username: str | None):
    """Assign one or multiple task ids to a username"""
    client = PhabricatorClient()
    if not username:
        user = client.current_user()
    else:
        user = client.find_user_by_username(username)
        if not user:
            ctx.fail(f"User {username} was not found")
    for task_id in task_ids:
        client.assign_task_to_user(task_id=task_id, user_phid=user["phid"])


@cli.command(name="move")
@click.option(
    "--column",
    type=str,
    required=True,
    help="Name of destination column on the current project board",
)
@click.argument("task-id", type=Task.from_str)
@click.pass_context
def move_task(ctx, task_id: int, column: str | None):
    """Move a task on its current project board"""
    client = PhabricatorClient()
    if not (
        current_milestone := client.get_project_current_milestone(
            project_phid=os.environ["PHABRICATOR_DEFAULT_PROJECT_PHID"]
        )
    ):
        ctx.fail("Current milestone not found")
    current_milestone_columns = client.list_project_columns(
        project_phid=current_milestone["fields"]["proxyPHID"]
    )
    for col in current_milestone_columns:
        if col["fields"]["name"].lower() == column:
            column_phid = col["phid"]
            break
    else:
        ctx.fail(
            f"Column {column} not found in milestone {current_milestone['fields']['name']}"
        )
    client.move_task_to_column(task_id=task_id, column_phid=column_phid)
    if column["fields"]["name"].lower() == "done":
        client.mark_task_as_resolved(task_id)


@cli.command(name="comment")
@click.option(
    "--comment",
    type=str,
    help="Comment text or path to a text file containing the comment body. If not provided, an editor will be opened.",
)
@click.argument("task-id", type=Task.from_str)
@click.pass_context
def comment_on_task(ctx, task_id: int, comment: str | None):
    """Comment on a task"""
    client = PhabricatorClient()
    comment = text_from_cli_arg_or_fs_or_editor(comment)
    client.create_or_edit_task(task_id=task_id, params={"comment": comment})


if __name__ == "__main__":
    cli()
