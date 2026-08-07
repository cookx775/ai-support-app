from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.request import Request, urlopen

from databricks.sdk import WorkspaceClient

if __package__ in (None, ""):
    script_path = locals().get("__file__") or locals().get("filename")
    if script_path is None:
        raise RuntimeError("Unable to determine the Homework 2 application path")
    sys.path.insert(0, str(Path(script_path).resolve().parents[1]))

DEFAULT_APP_URL = "https://ai-support-app-7474657586545240.aws.databricksapps.com"


def verify_deployed_search(
    app_url: str,
    query: str,
    top_k: int,
    *,
    auth_headers: Mapping[str, str],
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    request_body = {"query": query.strip(), "top_k": max(1, min(int(top_k), 20))}
    endpoint = f"{app_url.rstrip('/')}/weather/search"
    headers = {**auth_headers, "Content-Type": "application/json"}
    request = Request(
        endpoint,
        data=json.dumps(request_body).encode(),
        headers=headers,
        method="POST",
    )

    with opener(request, timeout=300) as response:
        raw_body = response.read().decode(errors="replace")
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        response_url = response.geturl()

    evidence: dict[str, Any] = {
        "request": {
            "method": "POST",
            "path": "/weather/search",
            **request_body,
        },
        "http_status": status,
        "response_url": response_url,
        "content_type": content_type,
        "body_bytes": len(raw_body.encode()),
    }
    try:
        response_body = json.loads(raw_body)
    except json.JSONDecodeError:
        evidence["body_preview"] = raw_body[:500]
        return evidence

    matches = response_body.get("matches")
    if not isinstance(matches, list):
        raise TypeError("Deployed search response did not contain a matches list")
    evidence["response"] = response_body
    return evidence


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Verify the deployed Homework 2 REST endpoint")
    parser.add_argument("--app-url", default=DEFAULT_APP_URL)
    parser.add_argument("--query", default="flooding or severe weather risk")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    query = args.query.strip()
    if not query:
        parser.error("query must be non-empty")

    auth_headers = WorkspaceClient().config.authenticate()
    result = verify_deployed_search(
        args.app_url,
        query,
        args.top_k,
        auth_headers=auth_headers,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
