import json

from jobs.verify_deployed_rest import verify_deployed_search


class FakeResponse:
    status = 200

    @property
    def headers(self):
        return {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(
            {
                "matches": [
                    {
                        "document_id": "doc-1",
                        "location": "Chicago, IL",
                        "narrative_text": "Heavy rain is possible near rivers.",
                        "chunk_text": "Heavy rain is possible near rivers.",
                        "similarity": 0.81,
                    }
                ]
            }
        ).encode()

    def geturl(self):
        return "https://weather.example.com/weather/search"


def test_verify_deployed_search_posts_json_and_returns_credential_free_evidence():
    calls = []

    def fake_open(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    result = verify_deployed_search(
        "https://weather.example.com/",
        "flooding risk",
        5,
        auth_headers={"Authorization": "Bearer secret-token"},
        opener=fake_open,
    )

    request, timeout = calls[0]
    assert request.full_url == "https://weather.example.com/weather/search"
    assert request.method == "POST"
    assert json.loads(request.data) == {"query": "flooding risk", "top_k": 5}
    assert request.headers["Authorization"] == "Bearer secret-token"
    assert timeout == 300
    assert result["request"] == {
        "method": "POST",
        "path": "/weather/search",
        "query": "flooding risk",
        "top_k": 5,
    }
    assert result["http_status"] == 200
    assert result["content_type"] == "application/json"
    assert result["response_url"] == "https://weather.example.com/weather/search"
    assert result["response"]["matches"][0]["narrative_text"].startswith("Heavy rain")
    assert "Authorization" not in json.dumps(result)


def test_verify_deployed_search_reports_non_json_gateway_response_without_credentials():
    class EmptyResponse(FakeResponse):
        @property
        def headers(self):
            return {"Content-Type": "text/html"}

        def read(self):
            return b""

        def geturl(self):
            return "https://workspace.example.com/oidc/consume"

    result = verify_deployed_search(
        "https://weather.example.com",
        "flooding risk",
        5,
        auth_headers={"Authorization": "Bearer secret-token"},
        opener=lambda *_args, **_kwargs: EmptyResponse(),
    )

    assert result["http_status"] == 200
    assert result["response_url"] == "https://workspace.example.com/oidc/consume"
    assert result["content_type"] == "text/html"
    assert result["body_bytes"] == 0
    assert result["body_preview"] == ""
    assert "response" not in result
    assert "secret-token" not in json.dumps(result)
