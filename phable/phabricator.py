from datetime import timedelta
from importlib.metadata import version
from typing import Any, Literal, Optional, TypeVar

import requests

from .cache import cached
from .task import TaskStatus

T = TypeVar("T")


class Task(int):
    @classmethod
    def from_str(cls, value: str) -> int:
        return int(value.lstrip("T"))

    @classmethod
    def from_int(cls, value: int) -> str:
        return f"T{value}"


class PhabricatorClient:
    """Phabricator API HTTP client.

    See https://phabricator.wikimedia.org/conduit for the API capability and details.

    """

    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.timeout = 5
        self.base_headers = {
            "User-Agent": f"Phable/{version('phable_cli')} (https://pypi.org/project/phable-cli)",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _first(self, result_set: list[T]) -> T:
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
        headers |= self.base_headers
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
        self, params: dict[str, Any], task_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Create or edit (if a task_id is provided) a Maniphest task."""
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

    def enrich_task(
        self,
        task: dict[str, Any],
        with_author_owner: bool = False,
        with_tags: bool = False,
        with_subtasks: bool = False,
        with_parent: bool = False,
    ) -> dict[str, Any]:
        """Load additional data about a task.

        The given task is enriched AND returned.

        Some of the additional info that is loaded:
        * projects
        * subtasks
        * parent tasks
        """
        task["url"] = f"{self.base_url}/{Task.from_int(task['id'])}"

        if with_author_owner:
            self.enrich_task_with_author_owner(task)
        if with_tags:
            self.enrich_task_with_tags(task)
        if with_subtasks:
            self.enrich_task_with_subtasks(task)
        if with_parent:
            self.enrich_task_with_parent(task)
        return task

    def enrich_task_with_author_owner(self, task: dict[str, Any]) -> None:
        task["author"] = self.show_user(phid=task["fields"]["authorPHID"])
        if owner_id := task["fields"]["ownerPHID"]:
            owner = self.show_user(phid=owner_id)["fields"]["username"]
        else:
            owner = "Unassigned"
        task["owner"] = owner

    def enrich_task_with_tags(self, task: dict[str, Any]) -> None:
        if project_ids := task["attachments"]["projects"]["projectPHIDs"]:
            tags = [
                (
                    f"{project['fields']['parent']['name']} - {project['fields']['name']}"
                    if project["fields"]["parent"]
                    else project["fields"]["name"]
                )
                for project in self.show_projects(phids=project_ids)
            ]
        else:
            tags = []
        task["tags"] = tags

    def enrich_task_with_subtasks(self, task: dict[str, Any]) -> None:
        subtasks = self.find_subtasks(parent_id=task["id"])
        if not subtasks:
            subtasks = []
        for subtask in subtasks:
            if subtask_owner_id := subtask["fields"]["ownerPHID"]:
                owner = self.show_user(subtask_owner_id)["fields"]["username"]
            else:
                owner = ""
            subtask["owner"] = owner
        task["subtasks"] = subtasks

    def enrich_task_with_parent(self, task: dict[str, Any]) -> None:
        parent = self.find_parent_task(subtask_id=task["id"])
        task["parent"] = parent

    def find_tasks(
        self,
        column_phids: Optional[list[str]] = None,
        owner_phid: Optional[str] = None,
        backup_owner_phid: Optional[str] = None,
        project_phid: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        params = {
            "attachments[subscribers]": "true",
            "attachments[projects]": "true",
            "attachments[columns]": "true",
        }
        for i, column_phid in enumerate(column_phids):
            params[f"constraints[columnPHIDs][{i}]"] = column_phid
        if owner_phid:
            params["constraints[assigned][0]"] = owner_phid
        elif backup_owner_phid:
            params["constraints[custom.train.backup][0]"] = backup_owner_phid
        if project_phid:
            params["constraints[projects][0]"] = project_phid
        return self._make_request("maniphest.search", params=params)["result"]["data"]

    def find_subtasks(self, parent_id: int) -> list[dict[str, Any]]:
        """Return details of all Maniphest subtasks of the provided task id"""
        return self._make_request(
            "maniphest.search", params={"constraints[parentIDs][0]": parent_id}
        )["result"]["data"]

    @cached
    def find_parent_task(self, subtask_id: int) -> Optional[dict[str, Any]]:
        """Return details of the parent Maniphest task for the provided task id"""
        return self._first(
            self._make_request(
                "maniphest.search", params={"constraints[subtaskIDs][0]": subtask_id}
            )["result"]["data"]
        )

    def move_task_to_column(self, task_id: int, column_phid: str) -> dict[str, Any]:
        """Move the argument task to column of associated column id"""
        return self.create_or_edit_task(task_id=task_id, params={"column": column_phid})

    def set_task_status(self, task_id: int, status: TaskStatus) -> dict[str, Any]:
        return self.create_or_edit_task(task_id=task_id, params={"status": status})

    def mark_task_as_resolved(self, task_id: int) -> dict[str, Any]:
        """Set the status of the argument task to Resolved"""
        return self.set_task_status(task_id=task_id, status=TaskStatus.resolved)

    def mark_task_as_in_progress(self, task_id: int) -> dict[str, Any]:
        """Set the status of the argument task to in progress"""
        return self.set_task_status(task_id=task_id, status=TaskStatus.progress)

    def add_user_to_task_subscribers(
        self, task_id: int, user_phid: str
    ) -> dict[str, Any]:
        """Add the user to the list of the task subscribers"""
        return self.create_or_edit_task(
            task_id=task_id, params={"subscribers.add": [user_phid]}
        )

    @cached
    def show_user(self, phid: str) -> Optional[dict[str, Any]]:
        """Show details of a Maniphest user"""
        user = self._make_request(
            "user.search", params={"constraints[phids][0]": phid}
        )["result"]["data"]
        return self._first(user)

    @cached
    def show_projects(self, phids: list[str]) -> dict[str, Any]:
        """Show details of the provided Maniphest projects"""
        params = {}
        for i, phid in enumerate(phids):
            params[f"constraints[phids][{i}]"] = phid
        return self._make_request("project.search", params=params)["result"]["data"]

    @cached
    def current_user(self) -> dict[str, Any]:
        """Return details of the user associated with the phabricator API token"""
        return self._make_request("user.whoami")["result"]

    @cached
    def find_user_by_username(self, username: str) -> Optional[dict[str, Any]]:
        """Return user details of the user with the provided username"""
        user = self._make_request(
            "user.search", params={"constraints[usernames][0]": username}
        )["result"]["data"]
        return self._first(user)

    def assign_task_to_user(
        self, task_id: int, user_phid: str, secondary: bool = False
    ) -> dict[str, Any]:
        """Set the owner of the argument task to the argument user id"""
        field = "custom.train.backup" if secondary else "owner"
        value = [user_phid] if secondary else user_phid
        return self.create_or_edit_task(task_id=task_id, params={field: value})

    def assign_tag_to_task(self, task_id: int, tag_phid: str) -> dict[str, Any]:
        """Set the owner of the argument task to the argument user id"""
        return self.create_or_edit_task(
            task_id=task_id, params={"projects.add": [tag_phid]}
        )

    def edit_parent_tasks(
        self,
        task_id: int,
        parent_task_phids: list[str],
        action: Literal["add", "remove", "set"],
    ) -> dict[str, Any]:
        """Edit the parent_id of the argument task"""
        return self.create_or_edit_task(
            task_id=task_id, params={f"parents.{action}": parent_task_phids}
        )

    @cached(ttl=timedelta(days=1))
    def list_project_columns(
        self,
        project_phid: str,
    ) -> list[dict[str, Any]]:
        """Return the details of each column in a given project"""
        return self._make_request(
            "project.column.search", params={"constraints[projects][0]": project_phid}
        )["result"]["data"]

    @cached(ttl=timedelta(days=1))
    def get_project_current_milestone_phid(self, project_phid: str) -> Optional[str]:
        """Return the PHID of the current milestone associated with the given project.

        We assume that the current milestone is displayed on the project's
        board as the first non-hidden column.
        """
        columns = self.list_project_columns(project_phid)
        for column in columns:
            if column["fields"]["proxyPHID"] and not column["fields"]["isHidden"]:
                return column["fields"]["proxyPHID"]

    def get_main_project_or_milestone(self, milestone: bool, project_phid: str) -> str:
        """Returns either the given project, or the current milestone of the given project."""
        if not milestone:
            return project_phid

        target_project_phid = self.get_project_current_milestone_phid(
            project_phid=(project_phid)
        )

        if not target_project_phid:
            project = self.format_project_name(project_phid=project_phid)
            raise ValueError(f"Could not find a milestone in {project}")

        return target_project_phid

    def format_project_name(self, project_phid: str) -> str:
        project = self.show_projects(phids=[project_phid])[0]
        if project["fields"].get("parent"):
            parent_project_name = project["fields"]["parent"]["name"]
            return f"{parent_project_name} ({project['fields']['name']})"
        else:
            return project["fields"]["name"]

    @cached
    def find_column_in_project(self, project_phid: str, column_name: str) -> str:
        """Finds a column in a project.

        :raises ValueError if the column isn't found"""
        potential_target_columns = self.list_project_columns(project_phid=project_phid)

        for col in potential_target_columns:
            if col["fields"]["name"].lower() == column_name.lower():
                column_phid = col["phid"]
                break
        else:
            project_name = self.format_project_name(project_phid=project_phid)
            raise ValueError(
                f"Column {column_name} not found in milestone {project_name}"
            )
        return column_phid

    @cached
    def find_project_by_title(
        self, title: str, parent_phid: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        params = {"constraints[query]": f'title:"{title}"'}
        if parent_phid:
            params["constraints[parents][0]"] = parent_phid
        else:
            params["constraints[maxDepth]"] = "0"  # search for top-level project
        return self._first(
            self._make_request("project.search", params=params)["result"]["data"]
        )
