import responses
from click.testing import CliRunner

from phable.cli.list import list_tasks
from phable.phabricator import PhabricatorClient
from phable.tests.cli.conftest import add_response


def _add_find_tasks_mocks():
    """One find_tasks call followed by per-task enrichment (author + projects)."""
    add_response("maniphest.search", "show_task.json")
    add_response("user.search", "show_user.json")
    add_response("project.search", "show_projects.json")


@responses.activate
def test_list_tasks_oneline(client: PhabricatorClient):
    _add_find_tasks_mocks()

    result = CliRunner().invoke(list_tasks, ["--format", "oneline"], obj=client)

    assert result.exit_code == 0, result.output
    assert "T417698" in result.output
    assert (
        "Ensure select dse-k8s-hosted microservices can run active/active"
        in result.output
    )


@responses.activate
def test_list_tasks_with_owner_self(client: PhabricatorClient):
    """--owner self triggers user.whoami then two find_tasks calls (primary + backup owner)."""
    add_response("user.whoami", "current_user.json")
    # primary owner tasks
    add_response("maniphest.search", "tasks_for_current_user.json")
    # backup owner tasks (empty)
    add_response("maniphest.search", "tasks_where_user_is_backup_owner.json")

    result = CliRunner().invoke(
        list_tasks,
        ["--owner", "self", "--format", "oneline"],
        obj=client,
    )

    assert result.exit_code == 0, result.output
    assert "T418664" in result.output
    # user.whoami must have been called to resolve "self"
    assert any("user.whoami" in call.request.url for call in responses.calls)
    # find_tasks is called twice: once with owner_phid, once with backup_owner_phid
    maniphest_search_calls = [
        c for c in responses.calls if "maniphest.search" in c.request.url
    ]
    assert len(maniphest_search_calls) == 2
