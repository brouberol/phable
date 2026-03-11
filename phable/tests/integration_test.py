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


@pytest.mark.integration
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