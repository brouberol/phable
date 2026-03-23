"""Integration tests requiring a live Phabricator instance.

Run with:
    poetry run pytest -m integration
"""

import pprint

import pytest

from phable.config import config
from phable.phabricator import PhabricatorClient


@pytest.fixture
def client():
    return PhabricatorClient(config.phabricator_url, config.phabricator_token)


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
    print(f"\nComparing columns between '{previous['fields']['name']}' and '{current['fields']['name']}'")

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
        assert milestone["fields"]["parent"]["phid"] == config.phabricator_default_project_phid