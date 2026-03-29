"""Integration tests requiring a live Phabricator instance.

Run with:
    poetry run pytest -m exploratory
"""

import json
import pprint
from pathlib import Path

import pytest

from phable.cache import cache
from phable.config import config
from phable.phabricator import PhabricatorClient

CLI_FIXTURES_DIR = Path(__file__).parent / "cli" / "fixtures"


@pytest.fixture
def client():
    return PhabricatorClient(config.phabricator_url, config.phabricator_token)


def capture_response(client: PhabricatorClient) -> list:
    """Attach a session hook that records the next HTTP response body.

    Returns a one-element list that will be populated after the next API call.
    The cache is cleared first so that @cached methods always hit the network.
    """
    cache.clear_memory()
    captured = []
    client.session.hooks["response"].append(
        lambda r, *args, **kwargs: captured.append(r.json())
    )
    return captured


def save_fixture(name: str, data: dict) -> None:
    (CLI_FIXTURES_DIR / name).write_text(json.dumps(data, indent=2))


@pytest.mark.exploratory
def test_capture_show_task_fixture(client):
    """Capture the raw HTTP response for T417698 used by the 'show' command integration tests.

    Run with:
        poetry run pytest -m exploratory -s phable/tests/exploratory_test.py::test_capture_show_task_fixture
    """
    captured = capture_response(client)
    client.show_task(417698)
    assert captured, "No HTTP response was captured"
    save_fixture("show_task.json", captured[0])


@pytest.mark.exploratory
def test_capture_show_user_fixture(client):
    """Capture show_user HTTP response for the author of T417698.

    Reads show_task.json to derive the authorPHID. Run after test_capture_show_task_fixture.
    """
    captured = capture_response(client)
    client.show_user(phid="PHID-USER-jwsqammdbw33izmv4f4r")
    assert captured, "No HTTP response was captured"
    save_fixture("show_user.json", captured[0])


@pytest.mark.exploratory
def test_capture_show_projects_fixture(client):
    """Capture show_projects HTTP response for the project tags of T417698.

    Reads show_task.json to derive the projectPHIDs. Run after test_capture_show_task_fixture.
    """
    project_phids = ["PHID-PROJ-nk6fdveuzkehlysztapo"]

    captured = capture_response(client)
    client.show_projects(phids=project_phids)
    assert captured, "No HTTP response was captured"
    save_fixture("show_projects.json", captured[0])


@pytest.mark.exploratory
def test_capture_find_subtasks_fixture(client):
    """Capture find_subtasks HTTP response for T417698.

    Run after test_capture_show_task_fixture.
    """
    captured = capture_response(client)
    client.find_subtasks(parent_id=417698)
    assert captured, "No HTTP response was captured"
    save_fixture("find_subtasks.json", captured[0])


@pytest.mark.exploratory
def test_capture_find_parent_task_fixture(client):
    """Capture find_parent_task HTTP response for T417698.

    Run after test_capture_show_task_fixture.
    """
    captured = capture_response(client)
    client.find_parent_task(subtask_id=417698)
    assert captured, "No HTTP response was captured"
    save_fixture("find_parent_task.json", captured[0])


@pytest.mark.exploratory
def test_find_tasks_in_project_columns(client):
    current_milestone_phid = client.get_project_current_milestone_phid(
        config.phabricator_default_project_phid
    )
    assert current_milestone_phid, "No active milestone found for the default project"

    results = client.find_tasks_in_project_columns(current_milestone_phid)

    pprint.pprint(results)

    for task, column_phid in results:
        assert task["type"] == "TASK"
        assert column_phid.startswith("PHID-PCOL-")


@pytest.mark.exploratory
def test_validate_and_build_column_map(client):
    milestones = client.find_milestones_for_project(
        parent_phid=config.phabricator_default_project_phid
    )
    assert len(milestones) >= 2, "Need at least 2 milestones to compare"

    previous, current = milestones[-2], milestones[-1]
    print(
        f"\nComparing columns between '{previous['fields']['name']}' and '{current['fields']['name']}'"
    )

    column_map = client.validate_and_build_column_map(
        source_phid=previous["phid"],
        target_phid=current["phid"],
    )

    pprint.pprint(column_map)

    assert len(column_map) > 0
    for source_phid, target_phid in column_map.items():
        assert source_phid.startswith("PHID-PCOL-")
        assert target_phid.startswith("PHID-PCOL-")
        assert source_phid != target_phid


@pytest.mark.exploratory
def test_find_milestones_for_project(client):
    milestones = client.find_milestones_for_project(
        parent_phid=config.phabricator_default_project_phid
    )

    pprint.pprint(milestones)

    assert len(milestones) > 0
    # Results must be sorted by milestone sequence number
    sequence_numbers = [m["fields"]["milestone"] for m in milestones]
    assert sequence_numbers == sorted(sequence_numbers)
    # Each entry must have the expected structure
    for milestone in milestones:
        assert milestone["type"] == "PROJ"
        assert isinstance(milestone["fields"]["milestone"], int)
        assert (
            milestone["fields"]["parent"]["phid"]
            == config.phabricator_default_project_phid
        )
