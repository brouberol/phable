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
def test_validate_and_build_column_map(project_columns_response, target_project_columns_response):
    # Source columns fetched first, then target columns
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=project_columns_response,
        )
    )
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=target_project_columns_response,
        )
    )

    client = PhabricatorClient(base_url, token)
    column_map = client.validate_and_build_column_map(
        source_phid="PHID-PROJ-source",
        target_phid="PHID-PROJ-target",
    )

    assert column_map == {
        "PHID-PCOL-backlog": "PHID-PCOL-target-backlog",
        "PHID-PCOL-inprogress": "PHID-PCOL-target-inprogress",
        "PHID-PCOL-done": "PHID-PCOL-target-done",
        "PHID-PCOL-reported": "PHID-PCOL-target-reported",
    }


@responses.activate
def test_validate_and_build_column_map_with_ignored(project_columns_response, target_project_columns_response):
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=project_columns_response,
        )
    )
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=target_project_columns_response,
        )
    )

    client = PhabricatorClient(base_url, token)
    column_map = client.validate_and_build_column_map(
        source_phid="PHID-PROJ-source2",
        target_phid="PHID-PROJ-target2",
        ignored_columns=("Reported",),
    )

    # "Reported" excluded from the map
    assert "PHID-PCOL-reported" not in column_map
    assert column_map == {
        "PHID-PCOL-backlog": "PHID-PCOL-target-backlog",
        "PHID-PCOL-inprogress": "PHID-PCOL-target-inprogress",
        "PHID-PCOL-done": "PHID-PCOL-target-done",
    }


@responses.activate
def test_validate_and_build_column_map_missing_column(project_columns_response):
    # Target is missing "In Progress" and "Done"
    target_with_missing = {
        "result": {
            "data": [
                {
                    "id": 2001,
                    "type": "PCOL",
                    "phid": "PHID-PCOL-target-backlog",
                    "fields": {"name": "Backlog", "proxyPHID": None, "isHidden": False},
                },
                {
                    "id": 2004,
                    "type": "PCOL",
                    "phid": "PHID-PCOL-target-reported",
                    "fields": {"name": "Reported", "proxyPHID": None, "isHidden": False},
                },
            ],
            "maps": {},
            "query": {"queryKey": None},
            "cursor": {"limit": 100, "after": None, "before": None, "order": None},
        },
        "error_code": None,
        "error_info": None,
    }
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=project_columns_response,
        )
    )
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=target_with_missing,
        )
    )

    client = PhabricatorClient(base_url, token)
    try:
        client.validate_and_build_column_map(
            source_phid="PHID-PROJ-source3",
            target_phid="PHID-PROJ-target3",
        )
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "In Progress" in str(e)
        assert "Done" in str(e)


@responses.activate
def test_find_tasks_in_project_columns(project_columns_response, tasks_in_column_response):
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=project_columns_response,
        )
    )
    # With no ignored columns, find_tasks is called once per column (Backlog, In Progress, Done, Reported)
    for _ in range(4):
        responses.add(
            responses.Response(
                method="POST",
                url=base_url + "api/maniphest.search",
                json=tasks_in_column_response,
            )
        )

    client = PhabricatorClient(base_url, token)
    results = client.find_tasks_in_project_columns("PHID-PROJ-nk6fdveuzkehlysztapo")

    # 4 columns × 1 task each = 4 (task, column_phid) pairs
    assert len(results) == 4
    for task, column_phid in results:
        assert task["type"] == "TASK"
        assert column_phid in {"PHID-PCOL-backlog", "PHID-PCOL-inprogress", "PHID-PCOL-done", "PHID-PCOL-reported"}


@responses.activate
def test_find_tasks_in_project_columns_with_ignored(project_columns_response, tasks_in_column_response):
    responses.add(
        responses.Response(
            method="POST",
            url=base_url + "api/project.column.search",
            json=project_columns_response,
        )
    )
    # Ignoring "Done" and "Reported": only Backlog and In Progress remain
    for _ in range(2):
        responses.add(
            responses.Response(
                method="POST",
                url=base_url + "api/maniphest.search",
                json=tasks_in_column_response,
            )
        )

    client = PhabricatorClient(base_url, token)
    # Use a different PHID to avoid cache hit from the previous test
    results = client.find_tasks_in_project_columns(
        "PHID-PROJ-azari57v5wl2i2koshdl",
        ignored_columns=("Done", "Reported"),
    )

    assert len(results) == 2
    for _, column_phid in results:
        assert column_phid in {"PHID-PCOL-backlog", "PHID-PCOL-inprogress"}


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

    milestones = client.find_milestones_for_project("PHID-PROJ-milestone1")
    assert len(milestones) == 3
    # Verify results are sorted by milestone sequence number
    assert [m["fields"]["milestone"] for m in milestones] == [35, 36, 37]
    assert milestones[0]["phid"] == "PHID-PROJ-milestone1"
    assert milestones[2]["phid"] == "PHID-PROJ-milestone3"
    assert milestones[2]["fields"]["status"] == "active"
