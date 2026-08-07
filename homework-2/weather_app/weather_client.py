from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

NWS_BASE_URL = "https://api.weather.gov"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "weather-intelligence-homework/1.0 (github.com/cookx775/ai-support-app)"


class WeatherClientError(RuntimeError):
    """Raised when a location cannot be resolved or weather data cannot be fetched."""


class LocationValidationError(WeatherClientError):
    """Raised when a requested location has an invalid or unresolvable shape."""


@dataclass(frozen=True)
class ResolvedLocation:
    label: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class WeatherDocument:
    id: str
    location: str
    latitude: float
    longitude: float
    source_type: str
    headline: str
    narrative_text: str
    issued_at: Optional[str]
    effective_at: Optional[str]
    content_hash: str
    payload: dict[str, Any]


class WeatherClient:
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
        timeout: float = 20.0,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if session is None:
            session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=("GET",),
            )
            session.mount("https://", HTTPAdapter(max_retries=retries))
        user_agent = user_agent or os.environ.get("WEATHER_USER_AGENT", DEFAULT_USER_AGENT)
        self._session = session
        self._headers = {"Accept": "application/geo+json", "User-Agent": user_agent}
        self._timeout = timeout
        self._sleeper = sleeper
        self._clock = clock
        self._geocode_cache: dict[str, ResolvedLocation] = {}
        self._last_geocode_at: Optional[float] = None
        self._geocode_lock = threading.Lock()

    def resolve_location(self, value: Any) -> ResolvedLocation:
        if isinstance(value, str):
            query = value.strip()
            if not query:
                raise LocationValidationError("Location strings cannot be empty")
            cache_key = query.casefold()
            cached = self._geocode_cache.get(cache_key)
            if cached is not None:
                return cached
            with self._geocode_lock:
                cached = self._geocode_cache.get(cache_key)
                if cached is not None:
                    return cached
                resolved = self._geocode(query)
                self._geocode_cache[cache_key] = resolved
                return resolved

        if isinstance(value, Mapping):
            if "lat" not in value or "lon" not in value:
                raise LocationValidationError("Coordinate objects require lat and lon")
            label = str(value.get("label") or f"{value['lat']},{value['lon']}")
            return self._coordinate_location(label, value["lat"], value["lon"])

        if isinstance(value, Sequence) and len(value) == 2:
            label = f"{value[0]},{value[1]}"
            return self._coordinate_location(label, value[0], value[1])

        raise LocationValidationError(
            "Locations must be city strings, coordinate objects, or [lat, lon]"
        )

    def _geocode(self, query: str) -> ResolvedLocation:
        if self._last_geocode_at is not None:
            elapsed = self._clock() - self._last_geocode_at
            if elapsed < 1.0:
                self._sleeper(1.0 - elapsed)
        try:
            response = self._session.get(
                NOMINATIM_SEARCH_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "us",
                },
                headers={"User-Agent": self._headers["User-Agent"]},
                timeout=self._timeout,
            )
            self._last_geocode_at = self._clock()
            response.raise_for_status()
            candidates = response.json()
            if not isinstance(candidates, list) or not candidates:
                raise LocationValidationError(f"No US location found for {query!r}")
            return self._coordinate_location(query, candidates[0]["lat"], candidates[0]["lon"])
        except WeatherClientError:
            raise
        except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
            raise WeatherClientError(f"Unable to geocode {query!r}: {exc}") from exc

    @staticmethod
    def _coordinate_location(label: str, latitude: Any, longitude: Any) -> ResolvedLocation:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise LocationValidationError("Latitude and longitude must be numeric") from exc
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise LocationValidationError("Latitude or longitude is outside its valid range")
        return ResolvedLocation(label.strip(), latitude, longitude)

    def fetch_documents(self, location: ResolvedLocation, limit: int = 50) -> list[WeatherDocument]:
        limit = max(1, min(int(limit), 50))
        point = f"{location.latitude:.4f},{location.longitude:.4f}"
        point_url = f"{NWS_BASE_URL}/points/{point}"

        try:
            point_payload = self._get_json(point_url)
            forecast_url = point_payload["properties"]["forecast"]
            forecast_payload = self._get_json(forecast_url)
            alerts_url = f"{NWS_BASE_URL}/alerts/active"
            alerts_payload = self._get_json(alerts_url, params={"point": point})
        except (KeyError, TypeError, requests.RequestException, ValueError) as exc:
            raise WeatherClientError(
                f"Unable to fetch NWS data for {location.label}: {exc}"
            ) from exc

        documents = self._normalize_alerts(location, alerts_url, alerts_payload)
        documents.extend(self._normalize_forecasts(location, forecast_url, forecast_payload))
        return documents[:limit]

    def _get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        response = self._session.get(
            url,
            headers=self._headers,
            timeout=self._timeout,
            **kwargs,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("expected a JSON object")
        return payload

    @staticmethod
    def _normalize_alerts(
        location: ResolvedLocation,
        source_url: str,
        payload: dict[str, Any],
    ) -> list[WeatherDocument]:
        documents: list[WeatherDocument] = []
        for feature in payload.get("features", []):
            properties = feature.get("properties") or {}
            narrative = "\n\n".join(
                part.strip()
                for part in (properties.get("description"), properties.get("instruction"))
                if isinstance(part, str) and part.strip()
            )
            if not narrative:
                continue
            document_id = feature.get("id") or _stable_hash(
                "alert",
                location.latitude,
                location.longitude,
                properties.get("sent"),
                properties.get("event"),
            )
            documents.append(
                WeatherDocument(
                    id=str(document_id),
                    location=location.label,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    source_type="alert",
                    headline=(
                        properties.get("headline") or properties.get("event") or "Weather alert"
                    ),
                    narrative_text=narrative,
                    issued_at=properties.get("sent"),
                    effective_at=properties.get("effective"),
                    content_hash=_content_hash(narrative),
                    payload={"source_url": source_url, "item": feature},
                )
            )
        return documents

    @staticmethod
    def _normalize_forecasts(
        location: ResolvedLocation,
        source_url: str,
        payload: dict[str, Any],
    ) -> list[WeatherDocument]:
        properties = payload.get("properties") or {}
        issued_at = properties.get("generatedAt") or properties.get("updateTime")
        documents: list[WeatherDocument] = []
        for period in properties.get("periods", []):
            narrative = period.get("detailedForecast")
            if not isinstance(narrative, str) or not narrative.strip():
                continue
            narrative = narrative.strip()
            identity = _stable_hash(
                f"{location.latitude:.4f}",
                f"{location.longitude:.4f}",
                period.get("startTime"),
                period.get("name"),
            )
            documents.append(
                WeatherDocument(
                    id=f"forecast:{identity}",
                    location=location.label,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    source_type="forecast",
                    headline=period.get("name") or "Forecast",
                    narrative_text=narrative,
                    issued_at=issued_at,
                    effective_at=period.get("startTime"),
                    content_hash=_content_hash(narrative),
                    payload={"source_url": source_url, "item": period},
                )
            )
        return documents


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_hash(*parts: Any) -> str:
    encoded = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
