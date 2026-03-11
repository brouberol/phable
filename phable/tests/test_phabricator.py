import json
from urllib.parse import parse_qs

import responses

from phable.phabricator import PhabricatorClient

base_url = "http://example.net/"
token = "my_token"


@responses.activate
def test_show_task(simple_task_response):
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/maniphest.search",
            json=simple_task_response,
        )
    )

    client = PhabricatorClient(base_url, token)

    task = client.show_task(390836)
    assert task["id"] == 390836


@responses.activate
def test_find_tasks_with_statuses(simple_task_response):
    captured_request = {}

    def callback(request):
        captured_request["body"] = request.body
        return (200, {}, json.dumps(simple_task_response))

    responses.add_callback(
        responses.POST,
        base_url + "api/maniphest.search",
        callback=callback,
        content_type="application/json",
    )

    client = PhabricatorClient(base_url, token)

    client.find_tasks(
        column_phids=["PHID-PCOL-123"],
        project_phid="PHID-PROJ-123",
        status=["open", "duplicate"],
    )

    request_body = captured_request["body"]
    if isinstance(request_body, bytes):
        request_body = request_body.decode()
    payload = parse_qs(request_body)

    assert payload["constraints[columnPHIDs][0]"] == ["PHID-PCOL-123"]
    assert payload["constraints[projects][0]"] == ["PHID-PROJ-123"]
    assert payload["constraints[statuses][0]"] == ["open"]
    assert payload["constraints[statuses][1]"] == ["duplicate"]


@responses.activate
def test_find_milestones_for_project(milestones_response):
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.search",
            json=milestones_response,
        )
    )

    client = PhabricatorClient(base_url, token)

    milestones = client.find_milestones_for_project("PHID-PROJ-r456pnp5exj6uphuhwy6")
    assert len(milestones) == 3
    # Verify results are sorted by milestone sequence number
    assert [m["fields"]["milestone"] for m in milestones] == [35, 36, 37]
    assert milestones[0]["phid"] == "PHID-PROJ-milestone1"
    assert milestones[2]["phid"] == "PHID-PROJ-milestone3"
    assert milestones[2]["fields"]["status"] == "active"
