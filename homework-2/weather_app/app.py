from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from flask import Flask, jsonify, request

from weather_app.embeddings import MODEL_NAME, EmbeddingService
from weather_app.repository import WeatherRepository
from weather_app.weather_client import (
    LocationValidationError,
    WeatherClient,
    WeatherClientError,
)

logger = logging.getLogger("weather-intelligence")


def create_app(
    repository: Optional[Any] = None,
    weather_client: Optional[Any] = None,
    embeddings: Optional[Any] = None,
    initialize_schema: bool = True,
) -> Flask:
    app = Flask(__name__)
    repository = repository or WeatherRepository()
    weather_client = weather_client or WeatherClient()
    embeddings = embeddings or EmbeddingService()

    if initialize_schema:
        repository.initialize_schema()

    @app.get("/")
    def index():
        return jsonify(
            {
                "service": "Weather Intelligence",
                "model": MODEL_NAME,
                "endpoints": {
                    "sync": "POST /weather/sync",
                    "search": "POST /weather/search",
                    "health": "GET /healthz",
                },
                "sources": {
                    "weather": "National Weather Service",
                    "geocoding": "OpenStreetMap Nominatim",
                },
            }
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.post("/weather/sync")
    def sync_weather():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400
        locations = body.get("locations")
        if not isinstance(locations, list) or not locations:
            return jsonify({"error": "locations must be a non-empty list"}), 400
        try:
            limit = _clamped_integer(body.get("limit", 50), minimum=1, maximum=50)
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400

        synced = 0
        resolved_locations = []
        errors = []
        validation_failures = 0
        successful_locations = 0

        for requested_location in locations:
            try:
                resolved = weather_client.resolve_location(requested_location)
                documents = weather_client.fetch_documents(resolved, limit=limit)
                synced += repository.upsert_documents(documents)
                successful_locations += 1
                resolved_locations.append(
                    {
                        "label": resolved.label,
                        "latitude": resolved.latitude,
                        "longitude": resolved.longitude,
                        "documents": len(documents),
                    }
                )
            except LocationValidationError as exc:
                validation_failures += 1
                errors.append({"location": requested_location, "error": str(exc)})
            except WeatherClientError as exc:
                errors.append({"location": requested_location, "error": str(exc)})
            except Exception:
                logger.exception("Weather sync failed for %r", requested_location)
                errors.append({"location": requested_location, "error": "Lakebase write failed"})

        response = {
            "synced": synced,
            "resolved_locations": resolved_locations,
            "errors": errors,
        }
        if successful_locations:
            return jsonify(response)
        if validation_failures == len(locations):
            return jsonify(response), 400
        return jsonify(response), 502

    @app.post("/weather/search")
    def search_weather():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400
        query = body.get("query")
        if not isinstance(query, str) or not query.strip():
            return jsonify({"error": "query must be a non-empty string"}), 400
        query = query.strip()
        try:
            top_k = _clamped_integer(body.get("top_k", 5), minimum=1, maximum=20)
        except (TypeError, ValueError):
            return jsonify({"error": "top_k must be an integer"}), 400

        vector = embeddings.embed_query(query)
        matches = [_json_safe(match) for match in repository.search(vector, top_k)]
        return jsonify({"query": query, "top_k": top_k, "matches": matches})

    return app


def _clamped_integer(value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise TypeError("boolean values are not integers")
    number = int(value)
    return max(minimum, min(number, maximum))


def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result
