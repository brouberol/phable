import json
from pathlib import Path

import pytest


@pytest.fixture
def simple_task_response():
    return json.load(open(Path(__file__).parent / Path("fixtures/simple_task.json")))


@pytest.fixture
def milestones_response():
    return json.load(open(Path(__file__).parent / Path("fixtures/milestones.json")))
