from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    script_path = locals().get("__file__") or locals().get("filename")
    if script_path is None:
        raise RuntimeError("Unable to determine the Homework 2 application path")
    sys.path.insert(0, str(Path(script_path).resolve().parents[1]))

from weather_app.repository import WeatherRepository
from weather_app.weather_client import WeatherClient, WeatherClientError

DEFAULT_LOCATIONS = ["Chicago, IL", "Austin, TX"]


def run_sync(
    repository: Any,
    weather_client: Any,
    locations: list[str],
    limit: int = 50,
) -> dict[str, Any]:
    repository.initialize_schema()
    synced = 0
    resolved_locations = []
    errors = []

    for requested_location in locations:
        try:
            resolved = weather_client.resolve_location(requested_location)
            documents = weather_client.fetch_documents(resolved, limit=limit)
            synced += repository.upsert_documents(documents)
            resolved_locations.append(
                {
                    "label": resolved.label,
                    "latitude": resolved.latitude,
                    "longitude": resolved.longitude,
                    "documents": len(documents),
                }
            )
        except WeatherClientError as exc:
            errors.append({"location": requested_location, "error": str(exc)})

    return {
        "synced": synced,
        "resolved_locations": resolved_locations,
        "errors": errors,
    }


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Sync NWS documents into Homework 2 Lakebase")
    parser.add_argument("--location", action="append", dest="locations")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)

    limit = max(1, min(args.limit, 50))
    result = run_sync(
        repository=WeatherRepository(),
        weather_client=WeatherClient(),
        locations=args.locations or DEFAULT_LOCATIONS,
        limit=limit,
    )
    print(json.dumps(result, sort_keys=True))
    if result["errors"] and not result["resolved_locations"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
