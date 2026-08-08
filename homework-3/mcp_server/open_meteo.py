"""Open-Meteo adapter for the weather prediction MCP server."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherServiceError(RuntimeError):
    """Raised when input or an upstream response cannot produce weather data."""


@dataclass(frozen=True)
class ResolvedLocation:
    requested: str
    name: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "name": self.name,
            "country_code": self.country_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
        }


class OpenMeteoClient:
    """Resolve locations and return normalized Open-Meteo weather data."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = 20.0,
        max_attempts: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session = session or requests.Session()
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._sleeper = sleeper
        self._locations: dict[str, ResolvedLocation] = {}

    def get_current_weather(self, location: str) -> dict[str, Any]:
        """Return current conditions for a city or postal-code query."""
        resolved = self.resolve_location(location)
        payload = self._get_json(
            FORECAST_URL,
            params={
                "latitude": resolved.latitude,
                "longitude": resolved.longitude,
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "precipitation,weather_code,wind_speed_10m"
                ),
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": resolved.timezone,
            },
        )
        try:
            current = payload["current"]
            units = payload["current_units"]
            return {
                "status": "success",
                "location": resolved.as_dict(),
                "observed_at": current["time"],
                "conditions": describe_weather_code(current["weather_code"]),
                "temperature": _measurement(current["temperature_2m"], units["temperature_2m"]),
                "apparent_temperature": _measurement(
                    current["apparent_temperature"], units["apparent_temperature"]
                ),
                "relative_humidity": _measurement(
                    current["relative_humidity_2m"], units["relative_humidity_2m"]
                ),
                "precipitation": _measurement(current["precipitation"], units["precipitation"]),
                "wind_speed": _measurement(current["wind_speed_10m"], "mph"),
                "source": "Open-Meteo",
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherServiceError("Open-Meteo returned incomplete current conditions") from exc

    def get_forecast(self, location: str, days: int = 7) -> dict[str, Any]:
        """Return one to sixteen normalized daily forecasts."""
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 16:
            raise WeatherServiceError("Forecast days must be an integer from 1 through 16")
        resolved = self.resolve_location(location)
        payload = self._get_json(
            FORECAST_URL,
            params={
                "latitude": resolved.latitude,
                "longitude": resolved.longitude,
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,precipitation_sum,wind_speed_10m_max"
                ),
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": resolved.timezone,
                "forecast_days": days,
            },
        )
        try:
            daily = payload["daily"]
            normalized = [
                {
                    "date": values[0],
                    "conditions": describe_weather_code(values[1]),
                    "temperature_high": _measurement(values[2], "°F"),
                    "temperature_low": _measurement(values[3], "°F"),
                    "precipitation_probability": _measurement(values[4], "%"),
                    "precipitation": _measurement(values[5], "inch"),
                    "wind_speed_max": _measurement(values[6], "mph"),
                }
                for values in zip(
                    daily["time"],
                    daily["weather_code"],
                    daily["temperature_2m_max"],
                    daily["temperature_2m_min"],
                    daily["precipitation_probability_max"],
                    daily["precipitation_sum"],
                    daily["wind_speed_10m_max"],
                    strict=True,
                )
            ][:days]
            if not normalized:
                raise ValueError("daily forecast is empty")
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherServiceError("Open-Meteo returned an incomplete daily forecast") from exc
        return {
            "status": "success",
            "location": resolved.as_dict(),
            "timezone": payload.get("timezone", resolved.timezone),
            "forecast_days": len(normalized),
            "days": normalized,
            "source": "Open-Meteo",
        }

    def get_weather_recommendation(self, location: str, forecast_date: str) -> dict[str, Any]:
        """Return explainable, rule-based weather guidance for an ISO local date."""
        try:
            requested_date = date.fromisoformat(forecast_date).isoformat()
        except (TypeError, ValueError) as exc:
            raise WeatherServiceError("Date must use YYYY-MM-DD format") from exc

        forecast = self.get_forecast(location, days=16)
        day = next((item for item in forecast["days"] if item["date"] == requested_date), None)
        if day is None:
            raise WeatherServiceError(
                f"Date {requested_date} is outside the available forecast horizon"
            )

        probability = day["precipitation_probability"]["value"]
        precipitation = day["precipitation"]["value"]
        high = day["temperature_high"]["value"]
        low = day["temperature_low"]["value"]
        wind = day["wind_speed_max"]["value"]
        flags = {
            "umbrella_needed": probability >= 40 or precipitation >= 0.05,
            "jacket_recommended": low < 55 or high < 65,
            "heat_caution": high >= 90,
            "wind_caution": wind >= 25,
        }
        reasons = []
        if flags["umbrella_needed"]:
            reasons.append(
                "Umbrella recommended: precipitation probability is "
                f"{probability}% and forecast amount is {precipitation} inch."
            )
        if flags["jacket_recommended"]:
            reasons.append(f"Jacket recommended: forecast high is {high}°F and low is {low}°F.")
        if flags["heat_caution"]:
            reasons.append(f"Heat caution: forecast high is {high}°F.")
        if flags["wind_caution"]:
            reasons.append(f"Wind caution: maximum wind is {wind} mph.")
        if not reasons:
            reasons.append("No recommendation thresholds were met.")

        return {
            "status": "success",
            "location": forecast["location"],
            "timezone": forecast["timezone"],
            "date": requested_date,
            "recommendations": flags,
            "summary": _recommendation_summary(flags),
            "reasons": reasons,
            "forecast": day,
            "source": "Open-Meteo",
            "method": "Deterministic thresholds documented in README.md",
        }

    def compare_weather(self, locations: list[str], forecast_date: str) -> dict[str, Any]:
        """Compare the same forecast date across two to five location queries."""
        if not isinstance(locations, list) or not 2 <= len(locations) <= 5:
            raise WeatherServiceError("Comparison requires a list of two through five locations")
        try:
            requested_date = date.fromisoformat(forecast_date).isoformat()
        except (TypeError, ValueError) as exc:
            raise WeatherServiceError("Date must use YYYY-MM-DD format") from exc

        comparisons = []
        errors = []
        for location in locations:
            try:
                recommendation = self.get_weather_recommendation(location, requested_date)
                comparisons.append(
                    {
                        "location": recommendation["location"],
                        "timezone": recommendation["timezone"],
                        "forecast": recommendation["forecast"],
                        "recommendations": recommendation["recommendations"],
                    }
                )
            except WeatherServiceError as exc:
                errors.append({"location": location, "message": str(exc)})

        if not comparisons:
            raise WeatherServiceError("No comparison locations produced forecast data")

        def names_by(key: str) -> list[str]:
            return [
                item["location"]["name"]
                for item in sorted(
                    comparisons,
                    key=lambda item: item["forecast"][key]["value"],
                    reverse=key == "temperature_high",
                )
            ]

        return {
            "status": "partial" if errors else "success",
            "date": requested_date,
            "comparisons": comparisons,
            "rankings": {
                "warmest_first": names_by("temperature_high"),
                "lowest_precipitation_risk_first": names_by("precipitation_probability"),
                "least_windy_first": names_by("wind_speed_max"),
            },
            "errors": errors,
            "source": "Open-Meteo",
        }

    def resolve_location(self, location: str) -> ResolvedLocation:
        """Resolve and cache the first canonical match for a location query."""
        if not isinstance(location, str) or not location.strip():
            raise WeatherServiceError("Location must be a non-empty city or postal code")
        requested = location.strip()
        cache_key = requested.casefold()
        if cache_key in self._locations:
            return self._locations[cache_key]

        payload = self._get_json(
            GEOCODING_URL,
            params={"name": requested, "count": 1, "language": "en", "format": "json"},
        )
        try:
            item = payload["results"][0]
            parts = [item["name"], item.get("admin1"), item.get("country")]
            resolved = ResolvedLocation(
                requested=requested,
                name=", ".join(part for part in parts if part),
                country_code=item.get("country_code", ""),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                timezone=item["timezone"],
            )
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise WeatherServiceError(f"No location found for {requested!r}") from exc
        self._locations[cache_key] = resolved
        return resolved

    def _get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        for attempt in range(self._max_attempts):
            try:
                response = self._session.get(url, timeout=self._timeout, **kwargs)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise TypeError("expected a JSON object")
                return payload
            except (requests.RequestException, TypeError, ValueError) as exc:
                if attempt + 1 >= self._max_attempts:
                    raise WeatherServiceError("Open-Meteo is temporarily unavailable") from exc
                self._sleeper(0.5 * (2**attempt))
        raise AssertionError("retry loop exited unexpectedly")


def describe_weather_code(code: Any) -> str:
    """Translate a WMO weather code into a stable human-readable label."""
    try:
        normalized = int(code)
    except (TypeError, ValueError):
        return "Unknown conditions"
    return WMO_DESCRIPTIONS.get(normalized, f"Unknown conditions (WMO code {normalized})")


def _measurement(value: Any, unit: str) -> dict[str, Any]:
    return {"value": value, "unit": unit}


def _recommendation_summary(flags: dict[str, bool]) -> str:
    items = []
    if flags["umbrella_needed"]:
        items.append("an umbrella")
    if flags["jacket_recommended"]:
        items.append("a jacket")

    if len(items) == 2:
        summary = f"Bring {items[0]} and {items[1]}"
    elif items:
        summary = f"Bring {items[0]}"
    else:
        summary = "No umbrella or jacket is indicated"

    cautions = []
    if flags["heat_caution"]:
        cautions.append("heat")
    if flags["wind_caution"]:
        cautions.append("strong winds")
    if len(cautions) == 2:
        summary += f"; use caution for {cautions[0]} and {cautions[1]}"
    elif cautions:
        summary += f"; use caution in {cautions[0]}"
    return summary + "."
