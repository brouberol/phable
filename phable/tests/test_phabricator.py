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
