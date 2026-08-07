from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    script_path = locals().get("__file__") or locals().get("filename")
    if script_path is None:
        raise RuntimeError("Unable to determine the Homework 2 application path")
    sys.path.insert(0, str(Path(script_path).resolve().parents[1]))

from weather_app.embeddings import EmbeddingService
from weather_app.repository import WeatherRepository


def run_search(
    repository: Any,
    embedding_service: Any,
    query: str,
    top_k: int = 5,
) -> dict[str, Any]:
    vector = embedding_service.embed_query(query.strip())
    matches = [_json_safe(row) for row in repository.search(vector, top_k)]
    return {"query": query.strip(), "top_k": top_k, "matches": matches}


def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Search Homework 2 weather vectors")
    parser.add_argument("query", nargs="?", default="flooding or severe weather risk")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    query = args.query.strip()
    if not query:
        parser.error("query must be non-empty")
    top_k = max(1, min(args.top_k, 20))
    result = run_search(
        repository=WeatherRepository(),
        embedding_service=EmbeddingService(),
        query=query,
        top_k=top_k,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
