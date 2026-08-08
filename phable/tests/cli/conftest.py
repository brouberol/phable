import json
from pathlib import Path

import pytest
import responses

from phable.cache import cache
from phable.phabricator import PhabricatorClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_URL = "http://example.net/"
TOKEN = "test_token"


def add_response(endpoint: str, fixture: str):
    responses.add(
        responses.POST, BASE_URL + "api/" + endpoint, json=load_fixture(fixture)
    )


def load_fixture(name: str) -> dict:
    """Load a fixture file, skipping the test if it hasn't been captured yet."""
    path = FIXTURES_DIR / name
    if not path.exists():
        pytest.skip(
            f"Fixture '{name}' not found — run the corresponding exploratory capture test first"
        )
    return json.loads(path.read_text())


@pytest.fixture(autouse=True)
def clear_cache():
    """Prevent stale cache entries from suppressing HTTP calls between tests."""
    cache.clear_memory()
    yield
    cache.clear_memory()


@pytest.fixture
def client() -> PhabricatorClient:
    return PhabricatorClient(BASE_URL, TOKEN)
