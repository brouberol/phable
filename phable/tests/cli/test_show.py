import responses
from click.testing import CliRunner

from phable.cli.show import show_task
from phable.phabricator import PhabricatorClient
from phable.tests.cli.conftest import load_fixture, BASE_URL


def _add_show_mocks():
    add_response(endpoint="maniphest.search", fixture="show_task.json")
    add_response(endpoint="user.search", fixture="show_user.json")
    add_response(endpoint="project.search", fixture="show_projects.json")
    add_response(endpoint="maniphest.search", fixture="find_subtasks.json")
    add_response(endpoint="maniphest.search", fixture="find_parent_task.json")


def add_response(endpoint: str, fixture: str):
    responses.add(
        responses.POST, BASE_URL + "api/" + endpoint, json=load_fixture(fixture)
    )


@responses.activate
def test_show_task_plain(client: PhabricatorClient):
    _add_show_mocks()

    result = CliRunner().invoke(show_task, ["T417698"], obj=client)

    assert result.exit_code == 0, result.output
    assert "T417698" in result.output
    assert (
        "Ensure select dse-k8s-hosted microservices can run active/active"
        in result.output
    )
    assert "bking" in result.output


@responses.activate
def test_show_task_oneline(client: PhabricatorClient):
    _add_show_mocks()

    result = CliRunner().invoke(
        show_task, ["T417698", "--format", "oneline"], obj=client
    )

    assert result.exit_code == 0, result.output
    assert "T417698" in result.output
    assert (
        "Ensure select dse-k8s-hosted microservices can run active/active"
        in result.output
    )
    assert "Resolved" in result.output
