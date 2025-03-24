import os
import tempfile
import subprocess
import json

from typing import Any
from functools import cache
from pathlib import Path

import requests
import click


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


class PhabricatorClient:
    def __init__(self):
        self.base_url = os.environ["PHABRICATOR_URL"].rstrip("/")
        self.token = os.environ["PHABRICATOR_TOKEN"]
        self.session = requests.Session()
        self.timeout = 5

        if not self.base_url or not self.token:
            raise ValueError(
                "PHABRICATOR_URL and PHABRICATOR_TOKEN must be set in your envionment"
            )

    def _first(self, result_set: list):
        if result_set:
            return result_set[0]

    def _make_request(
        self,
        path: str,
        params: dict[str, Any] = None,
        headers: dict[str, str] = None,
    ) -> dict[str, Any]:
        """Helper method to make API requests"""
        headers = headers or {}
        headers |= {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        params = params or {}
        data = {}
        data["api.token"] = self.token
        data["output"] = "json"
        data |= params

        try:
            response = self.session.post(
                f"{self.base_url}/api/{path}",
                headers=headers,
                data=data,
                timeout=self.timeout,
            )

            response.raise_for_status()
            resp_json = response.json()
            if resp_json["error_code"]:
                raise Exception(f"API request failed: {resp_json}")
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def create_or_edit_task(
        self, params: dict[str, Any], task_id: int | None = None
    ) -> dict[str, Any]:
        raw_params = {}
        for i, (key, value) in enumerate(params.items()):
            raw_params[f"transactions[{i}][type]"] = key
            if isinstance(value, list):
                for j, subvalue in enumerate(value):
                    raw_params[f"transactions[{i}][value][{j}]"] = subvalue
            else:
                raw_params[f"transactions[{i}][value]"] = value
        if task_id:
            raw_params["objectIdentifier"] = task_id
        return self._make_request("maniphest.edit", params=raw_params)

    def show_task(self, task_id: int) -> dict[str, Any]:
        """Show a Maniphest task"""
        return self._make_request(
            "maniphest.search",
            params={
                "constraints[ids][0]": task_id,
                "attachments[subscribers]": "true",
                "attachments[projects]": "true",
                "attachments[columns]": "true",
            },
        )["result"]["data"][0]

    def find_tasks_with_parent(self, parent_id: int) -> list[dict[str, Any]]:
        return self._make_request(
            "maniphest.search", params={"constraints[parentIDs][0]": parent_id}
        )["result"]["data"]

    def find_subtask_parent(self, subtask_id: int) -> dict[str, Any] | None:
        return self._first(
            self._make_request(
                "maniphest.search", params={"constraints[subtaskIDs][0]": subtask_id}
            )["result"]["data"]
        )

    def move_task_to_column(self, task_id: int, column_phid: str) -> dict[str, Any]:
        return self.create_or_edit_task(task_id=task_id, params={"column": column_phid})

    @cache
    def show_user(self, phid: str) -> dict[str, Any] | None:
        """Show a Maniphest user"""
        user = self._make_request(
            "user.search", params={"constraints[phids][0]": phid}
        )["result"]["data"]
        return self._first(user)

    def show_projects(self, phids: list[str]) -> dict[str, Any]:
        """Show a Maniphest project"""
        params = {}
        for i, phid in enumerate(phids):
            params[f"constraints[phids][{i}]"] = phid
        return self._make_request("project.search", params=params)["result"]["data"]

    def current_user(self) -> dict[str, Any]:
        return self._make_request("user.whoami")["result"]

    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        user = self._make_request(
            "user.search", params={"constraints[usernames][0]": username}
        )["result"]["data"]
        return self._first(user)

    def assign_task_to_user(self, task_id: int, user_phid: int) -> dict[str, Any]:
        return self.create_or_edit_task(task_id=task_id, params={"owner": user_phid})

    def list_project_columns(
        self,
        project_phid: str,
    ) -> list[dict[str, Any]]:
        return self._make_request(
            "project.column.search", params={"constraints[projects][0]": project_phid}
        )["result"]["data"]

    def get_project_current_milestone(self, project_phid: str) -> dict[str, Any] | None:
        columns = self.list_project_columns(project_phid)
        for column in columns:
            if column["fields"]["proxyPHID"] and not column["fields"]["isHidden"]:
                return column



@cli.command(name="show")
@click.option("--format", type=click.Choice(("plain", "json")), default="plain")
@click.argument("task-id", type=Task.from_str)
def show_task(task_id: int, format: str = "plain"):
    """Show information about a Maniphest task"""
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
        subtasks = client.find_tasks_with_parent(parent_id=task_id)
        task["subtasks"] = subtasks
        if format == "json":
            click.echo(json.dumps(task))
        else:
            click.echo(f"URL: {client.base_url}/{Task.from_int(task_id)}")
            click.echo(f"Task: {Task.from_int(task_id)}")
            click.echo(f"Title: {task['fields']['name']}")
            click.echo(f"Author: {author['fields']['username']}")
            click.echo(f"Owner: {owner}")
            click.echo(f"Tags: {', '.join(tags)}")
            click.echo(f"Status: {task['fields']['status']['name']}")
            click.echo(f"Priority: {task['fields']['priority']['name']}")
            click.echo(f"Description: {task['fields']['description']['raw']}")
            if subtasks:
                click.echo("Subtasks:")
                for subtask in subtasks:
                    status = f"{'[x]' if subtask['fields']['status']['value'] == 'resolved' else '[ ]'}"
                    click.echo(
                        f"{status} - {Task.from_int(subtask['id'])} - {subtask['fields']['name']}"
                    )
    else:
        click.echo(f"Task T{task_id} not found")


@cli.command(name="create")
@click.option("--title", required=True, help="Title of the task")
@click.option("--description", help="Description of the task")
@click.option(
    "--priority",
    type=click.Choice(["unbreaknow", "high", "normal", "low", "needs-triage"]),
    help="Priority level of the task",
    default="normal",
)
@click.option("--project-tags", multiple=True, help="Project tags for the task")
@click.option("--parent-id", type=int, help="ID of parent task")
@click.option("--cc", multiple=True, help="Users to CC on the task")
@click.pass_context
def create_task(
    ctx,
    title: str,
    description: str,
    priority: str,
    project_tags: list[str],
    parent_id: str | None,
    cc: list[str],
):
    """Create a new Maniphest task"""
    client = PhabricatorClient()

    if not description:
        description_tmpfile = tempfile.NamedTemporaryFile(
            encoding="utf-8", mode="w", suffix=".md"
        )
        subprocess.run([os.environ["EDITOR"], description_tmpfile.name])
        description = Path(description_tmpfile.name).read_text()

    try:
        if (description_file := Path(description)).exists():
            description = description_file.read_text()
    except OSError:
        pass
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
@click.option("--username", required=False)
@click.argument("task-id", type=Task.from_str)
@click.pass_context
def assign_task(ctx, task_id: int, username: str | None):
    client = PhabricatorClient()
    if not username:
        user = client.current_user()
    else:
        user = client.find_user_by_username(username)
        if not user:
            ctx.fail(f"User {username} was not found")
    client.assign_task_to_user(task_id=task_id, user_phid=user["phid"])


@cli.command(name="move")
@click.option("--column", type=str, required=True)
@click.argument("task-id", type=Task.from_str)
@click.pass_context
def move_task(ctx, task_id: int, column: str | None):
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


if __name__ == "__main__":
    cli()
