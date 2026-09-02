import pytest
import requests
import responses

from tcgdex.client import API_HOSTS, fetch_json

PATH = "/v2/en/series/sv"


class TestFetchJson:
    @responses.activate
    def test_fails_over_when_host_unreachable(self):
        responses.add(
            responses.GET,
            f"{API_HOSTS[0]}{PATH}",
            body=requests.ConnectionError("connection refused"),
        )
        responses.add(
            responses.GET, f"{API_HOSTS[1]}{PATH}", json={"id": "sv"}, status=200
        )

        result = fetch_json(PATH)

        assert result == {"id": "sv"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_http_error_does_not_fail_over(self):
        responses.add(responses.GET, f"{API_HOSTS[0]}{PATH}", status=404)

        with pytest.raises(requests.HTTPError):
            fetch_json(PATH)

        assert len(responses.calls) == 1
