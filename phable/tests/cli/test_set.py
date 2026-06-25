from click.testing import CliRunner

from phable.cli.set import set_task_fields


class DummyPhabricatorClient:
    def __init__(self):
        self.edits = []
        self.projects = {
            "Data-Platform-SRE": {"phid": "PHID-PROJ-data-platform-sre"},
            "Kafka": {"phid": "PHID-PROJ-kafka"},
        }

    def find_project_by_title(self, title):
        return self.projects.get(title)

    def create_or_edit_task(self, task_id, params):
        self.edits.append({"task_id": task_id, "params": params})


def test_set_task_fields_adds_tags_to_projects():
    client = DummyPhabricatorClient()

    result = CliRunner().invoke(
        set_task_fields,
        [
            "T123456",
            "--tags",
            "Data-Platform-SRE",
            "--tags",
            "Kafka",
        ],
        obj=client,
    )

    assert result.exit_code == 0
    assert client.edits == [
        {
            "task_id": 123456,
            "params": {
                "projects.add": [
                    "PHID-PROJ-data-platform-sre",
                    "PHID-PROJ-kafka",
                ],
            },
        }
    ]
