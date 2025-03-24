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
        self.base_url = os.getenv("PHABRICATOR_URL").rstrip("/")
        self.token = os.getenv("PHABRICATOR_TOKEN")
        self.session = requests.Session()
        self.timeout = 5

        if not self.base_url or not self.token:
            raise ValueError(
                "PHABRICATOR_URL and PHABRICATOR_TOKEN must be set in your envionment"
            )

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
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def create_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a new Maniphest task"""
        raw_params = {}
        for i, (key, value) in enumerate(params.items()):
            raw_params[f"transactions[{i}][type]"] = key
            if isinstance(value, list):
                for j, subvalue in enumerate(value):
                    raw_params[f"transactions[{i}][value][{j}]"] = subvalue
            else:
                raw_params[f"transactions[{i}][value]"] = value
        return self._make_request("maniphest.edit", params=raw_params)

    def edit_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Edit a Maniphest task"""
        return self._make_request("maniphest.edit", params=params)

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

    @cache
    def show_user(self, phid: str) -> dict[str, Any]:
        """Show a Maniphest user"""
        return self._make_request(
            "user.search", params={"constraints[phids][0]": phid}
        )["result"]["data"][0]

    def show_projects(self, phids: list[str]) -> dict[str, Any]:
        """Show a Maniphest project"""
        params = {}
        for i, phid in enumerate(phids):
            params[f"constraints[phids][{i}]"] = phid
        return self._make_request("project.search", params=params)["result"]["data"]


@cli.command(name="show")
@click.option("--format", type=click.Choice(("plain", "json")), default="plain")
@click.argument("task-id", type=Task.from_str)
def show_task(task_id: int, format: str = "plain"):
    """Show information about a Maniphest task"""
    client = PhabricatorClient()
    if task := client.show_task(task_id):
        author = client.show_user(phid=task["fields"]["authorPHID"])
        if owner_id := task["fields"]["ownerPHID"]:
            owner = client.show_user(phid=owner_id)
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

    task = client.create_task(task_params)
    ctx.invoke(show_task, task_id=task["result"]["object"]["id"])


if __name__ == "__main__":
    cli()
