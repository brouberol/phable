import json

import pytest


@pytest.fixture
def simple_task_response():
    return json.load(open('fixtures/simple_task.json'))
