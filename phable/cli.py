import os
from typing import Any
import requests
import click
from functools import cache


@click.group()
def cli():
    """Phabricator Maniphest CLI"""
    pass


class PhabricatorClient:
    def __init__(self):
        self.base_url = os.getenv("PHABRICATOR_URL").rstrip("/")
        self.token = os.getenv("PHABRICATOR_TOKEN")
        self.session = requests.Session()
        self.timeout = 5

        if not self.base_url or not self.token:
            raise ValueError(
                "PHABRICATOR_URL and PHABRICATOR_TOKEN must be set in you envionment"
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

    def create_task(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Create a new Maniphest task"""
        return self._make_request("maniphest.create", params={"fields": fields})

    def edit_task(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Edit a Maniphest task"""
        return self._make_request("maniphest.edit", params={"fields": fields})

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



@cli.command()
@click.argument("task-id", type=int)
def show(task_id: int):
    """Show information about a Maniphest task"""
    client = PhabricatorClient()
    if task := client.show_task(task_id):
        author = client.show_user(phid=task["fields"]["authorPHID"])
        owner = client.show_user(phid=task["fields"]["ownerPHID"])
        if project_ids := task["attachments"]["projects"]["projectPHIDs"]:
            tags = [
                f"{project['fields']['parent']['name']} - {project['fields']['name']}"
                if project["fields"]["parent"]
                else project["fields"]["name"]
                for project in client.show_projects(phids=project_ids)
            ]
        else:
            tags = []
        click.echo(f"Task: T{task_id}")
        click.echo(f"Title: {task['fields']['name']}")
        click.echo(f"Author: {author['fields']['username']}")
        click.echo(f"Owner: {owner['fields']['username']}")
        click.echo(f"Tags: {', '.join(tags)}")
        click.echo(f"Status: {task['fields']['status']['name']}")
        click.echo(f"Priority: {task['fields']['priority']['name']}")
        click.echo(f"Description: {task['fields']['description']['raw']}")
    else:
        click.echo(f"Task T{task_id} not found")


if __name__ == "__main__":
    cli()
