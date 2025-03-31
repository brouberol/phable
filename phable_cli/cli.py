import atexit
import json
import re
from typing import Optional

import click
from click import Context

from .cache import cache
from .config import config
from .phabricator import PhabricatorClient
from .utils import text_from_cli_arg_or_fs_or_editor

VARIADIC = -1  # Used for click variadic arguments

# Dump the in-memory cache to disk when existing the CLI
atexit.register(cache.dump)


@click.group()
@click.version_option()
def cli():
    """Manage Phabricator tasks from the comfort of your terminal"""
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
    """Show task details

    \b
    Examples:
    $ phable show T123456                 # show task details as plaintext
    $ phable show T123456  --format=json  # show task details as json

    """
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
@click.option("--parent-id", type=Task.from_str, help="ID of parent task")
@click.option("--tags", multiple=True, help="Tags to associate to the task")
@click.option("--owner", help="The username of the task owner")
@click.pass_context
def create_task(
    ctx,
    title: str,
    description: Optional[str],
    priority: str,
    parent_id: Optional[str],
    tags: list[str],
    owner: Optional[str],
):
    """Create a new task

    \b
    Examples:
    \b
    # Create a task with a long description by writing it in your favorite text editor
    $ phable create --title 'A task'
    \b
    # Create a task with a long description by pointing it to a description file
    $ phable create --title 'A task' --description path/to/description.txt
    \b
    # Create a task with associated title, priority and desription
    $ phable create --title 'Do the thing!' --priority high --description 'Address the thing right now'
    \b
    # Create a task with a given parent
    $ phable create --title 'A subtask' --description 'Subtask description' --parent-id T123456
    \b
    # Create a task with an associated top-level project tag
    $ phable create --title 'A task' --tags 'Data-Platform-SRE'
    \b
    # Create a task with an associated sub-project tag
    $ phable create --title 'A task' --tags 'Data-Platform-SRE (2025.03.22 - 2025.04.11)
    \b
    # Create a task with an associated owner
    $ phable create --title 'A task' --owner brouberol

    """
    client = PhabricatorClient()
    description = text_from_cli_arg_or_fs_or_editor(description)
    task_params = {
        "title": title,
        "description": description,
        "projects.add": [config.phabricator_default_project_phid],
        "priority": priority,
    }

    tag_projects_phids = []
    for tag in tags:
        # The tag name can be a simple string, or "parent name (subproject name)"
        # In the case of the latter, we need to fetch details for both projects
        if match := re.match(
            r"(?P<parent>[\w\s\.-]+) \((?P<subproject>[\w\s+\.-]+)\)", tag
        ):
            parent_title = match.group("parent").strip()
            if parent_project := client.find_project_by_title(title=parent_title):
                parent_project_phid = parent_project["phid"]
            else:
                ctx.fail(f"Project {parent_project} not found")
            project_title = match.group("subproject").strip()
            if project := client.find_project_by_title(
                title=project_title, parent_phid=parent_project_phid
            ):
                tag_projects_phids.append(project["phid"])
            else:
                ctx.fail(f"Project {project_title} not found")
        # Simple project name with no subproject
        elif project := client.find_project_by_title(title=tag):
            tag_projects_phids.append(project["phid"])
        else:
            ctx.fail(f"Project {tag} not found")

    if tag_projects_phids:
        task_params["projects.add"] = tag_projects_phids

    if owner:
        if owner_user := client.find_user_by_username(username=owner):
            task_params["owner"] = owner_user["phid"]
        else:
            ctx.fail(f"User {owner} not found")

    if parent_id:
        parent = client.show_task(parent_id)
        task_params["parents.set"] = [parent["phid"]]

    task = client.create_or_edit_task(task_params)
    ctx.invoke(show_task, task_id=task["result"]["object"]["id"])


@cli.command(name="assign")
@click.option(
    "--username",
    required=False,
    help="The username to assign the task to. Self-assign the task if not provided.",
)
@click.argument("task-ids", type=Task.from_str, nargs=VARIADIC)
@click.pass_context
def assign_task(ctx, task_ids: list[int], username: Optional[str]):
    """Assign one or multiple task ids to a username

    \b
    Examples:
    $ phable assign T123456             # self assign task
    $ phable assign T123456  brouberol  # asign to username

    """
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
@click.option(
    "--milestone/--no-milestone",
    default=False,
    help=(
        "If --milestone is passed, the task will be moved onto the current project's associated "
        "milestone board, instead of the project board itself"
    ),
)
@click.argument("task-ids", type=Task.from_str, nargs=VARIADIC)
@click.pass_context
def move_task(
    ctx: Context, task_ids: list[int], column: Optional[str], milestone: bool
) -> None:
    """Move one or several task on their current project board

    If the task is moved to a 'Done' column, it will be automatically
    marked as 'Resolved' as well.

    \b
    Example:
    $ phable move T123456 --column 'In Progress'
    $ phable move T123456 T234567 --column 'Done'

    """
    try:
        client = PhabricatorClient()
        target_project_phid = client.get_main_project_or_milestone(
            milestone, config.phabricator_default_project_phid
        )
        target_column_phid = client.find_column_in_project(target_project_phid, column)

        for task_id in task_ids:
            client.move_task_to_column(task_id=task_id, column_phid=target_column_phid)
            if column.lower() == "done":
                client.mark_task_as_resolved(task_id)
    except ValueError as ve:
        ctx.fail(ve)


@cli.command(name="comment")
@click.option(
    "--comment",
    type=str,
    help="Comment text or path to a text file containing the comment body. If not provided, an editor will be opened.",
)
@click.argument("task-id", type=Task.from_str)
def comment_on_task(task_id: int, comment: Optional[str]):
    """Add a comment to a task

    \b
    Example:
    $ phable comment T123456 --comment 'hello'              # set comment body from the cli itself
    $ phable comment T123456 --comment path/to/comment.txt  # set comment body from a text file
    $ phable comment T123456                                # set comment body from your own text editor

    """
    client = PhabricatorClient()
    comment = text_from_cli_arg_or_fs_or_editor(comment)
    client.create_or_edit_task(task_id=task_id, params={"comment": comment})


@cli.command(name="subscribe")
@click.argument("task-ids", type=Task.from_str, nargs=VARIADIC)
@click.pass_context
def subscribe_to_task(ctx, task_ids: list[int]):
    """Subscribe to one or multiple task ids

    \b
    Examples:
    $ phable subscribe T123456
    $ phable subscribe T123456 T234567

    """
    client = PhabricatorClient()
    user = client.current_user()
    if not user:
        ctx.fail("Current user was not found")
    for task_id in task_ids:
        client.add_user_to_task_subscribers(task_id=task_id, user_phid=user["phid"])


if __name__ == "__main__":
    cli()
