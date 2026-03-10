from click.testing import CliRunner

from phable.cli.list import list_tasks
from phable.config import config


class DummyPhabricatorClient:
    def __init__(self):
        self.find_tasks_calls = []
        self.current_user_phid = "PHID-USER-123"
        self.target_project_phid = None

    def current_user(self):
        return {"phid": self.current_user_phid}

    def get_main_project_or_milestone(self, milestone: bool, project_phid: str) -> str:
        self.target_project_phid = project_phid
        return project_phid

    def find_tasks(
        self,
        column_phids=None,
        owner_phid=None,
        backup_owner_phid=None,
        project_phid=None,
        status=None,
    ):
        self.find_tasks_calls.append(
            {
                "column_phids": column_phids,
                "owner_phid": owner_phid,
                "backup_owner_phid": backup_owner_phid,
                "project_phid": project_phid,
                "status": status,
            }
        )
        return []

    def enrich_task(self, task):
        return task


def test_list_tasks_passes_statuses_and_queries_once_without_owner(monkeypatch):
    monkeypatch.setattr(config, "phabricator_default_project_phid", "PHID-PROJ-123")
    client = DummyPhabricatorClient()

    result = CliRunner().invoke(
        list_tasks,
        ["--status", "open", "--status", "duplicate"],
        obj=client,
    )

    assert result.exit_code == 0
    assert client.target_project_phid == "PHID-PROJ-123"
    assert client.find_tasks_calls == [
        {
            "column_phids": [],
            "owner_phid": None,
            "backup_owner_phid": None,
            "project_phid": "PHID-PROJ-123",
            "status": ["open", "duplicate"],
        }
    ]


def test_list_tasks_passes_statuses_to_owner_and_backup_queries(monkeypatch):
    monkeypatch.setattr(config, "phabricator_default_project_phid", "PHID-PROJ-123")
    client = DummyPhabricatorClient()

    result = CliRunner().invoke(
        list_tasks,
        ["--owner", "self", "--status", "open"],
        obj=client,
    )

    assert result.exit_code == 0
    assert client.find_tasks_calls == [
        {
            "column_phids": [],
            "owner_phid": "PHID-USER-123",
            "backup_owner_phid": None,
            "project_phid": "PHID-PROJ-123",
            "status": ["open"],
        },
        {
            "column_phids": [],
            "owner_phid": None,
            "backup_owner_phid": "PHID-USER-123",
            "project_phid": "PHID-PROJ-123",
            "status": ["open"],
        },
    ]
