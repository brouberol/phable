import re
from pathlib import Path
from typing import Optional

import click

from phable.cli.show import show_task
from phable.config import config
from phable.phabricator import PhabricatorClient
from phable.task import TASK_ID
from phable.utils import text_from_cli_arg_or_fs_or_editor


@click.command(name="create")
@click.option("--title", required=True, help="Title of the task")
@click.option(
    "--description",
    help="Task description or path to a file containing the description body. If not provided, an editor will be opened.",
)
@click.option(
    "--template",
    type=Path,
    help=(
        "Task description template file. If provided, the --description flag will be ignored "
        "and an editor will be opened, pre-filled with the template file content"
    ),
)
@click.option(
    "--priority",
    type=click.Choice(["unbreaknow", "high", "normal", "low", "needs-triage"]),
    help="Priority level of the task",
    default="normal",
)
@click.option("--parent-id", type=TASK_ID, help="ID of parent task")
@click.option("--tags", multiple=True, help="Tags to associate to the task")
@click.option("--cc", multiple=True, help="Subscribers to associate to the task")
@click.option("--owner", help="The username of the task owner")
@click.pass_context
@click.pass_obj
def create_task(
    client: PhabricatorClient,
    ctx: click.Context,
    title: str,
    description: Optional[str],
    template: Path,
    priority: str,
    parent_id: Optional[str],
    tags: list[str],
    cc: list[str],
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
    # Create a task with associated description template
    $ phable create --title 'Do the thing!' --template ./template.md
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
    \b
    # Create a task with an associated subscriber
    $ phable create --title 'A task' --cc brouberol

    """
    if template:
        if template.exists():
            description = template
            force_editor = True
        else:
            ctx.fail(f"Template file {template} does not exist")
    else:
        force_editor = False
    description = text_from_cli_arg_or_fs_or_editor(
        description, force_editor=force_editor
    )

    task_params = {
        "title": title,
        "description": description,
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
    else:
        task_params["projects.add"] = [config.phabricator_default_project_phid]

    if owner:
        if owner == "self":
            task_params["owner"] = client.current_user()["phid"]
        elif owner_user := client.find_user_by_username(username=owner):
            task_params["owner"] = owner_user["phid"]
        else:
            ctx.fail(f"User {owner} not found")

    if parent_id:
        parent = client.show_task(parent_id)
        task_params["parents.set"] = [parent["phid"]]

    cc_phids = []
    for username in cc:
        if user := client.find_user_by_username(username=username):
            cc_phids.append(user["phid"])
        else:
            ctx.fail(f"User {owner} not found")
    if cc_phids:
        task_params["subscribers.set"] = cc_phids

    task = client.create_or_edit_task(task_params)
    ctx.invoke(show_task, task_id=task["result"]["object"]["id"])
