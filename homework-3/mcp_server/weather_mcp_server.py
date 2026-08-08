"""FastMCP weather server backed by the separate Open-Meteo adapter."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from open_meteo import OpenMeteoClient, WeatherServiceError

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("weather-prediction-mcp")


def build_server(adapter: OpenMeteoClient | None = None) -> FastMCP:
    """Build the server, optionally injecting an adapter at the external API seam."""
    weather = adapter or OpenMeteoClient()
    server = FastMCP("weather-prediction")

    def call(operation: Callable[..., dict[str, Any]], *args: Any) -> dict[str, Any]:
        try:
            return operation(*args)
        except WeatherServiceError as exc:
            logger.warning("Weather request failed: %s", exc)
            return {
                "status": "error",
                "error": {"type": "weather_service_error", "message": str(exc)},
            }
        except Exception:
            logger.exception("Unexpected weather tool failure")
            return {
                "status": "error",
                "error": {
                    "type": "internal_error",
                    "message": "The weather service could not complete the request",
                },
            }

    @server.tool
    def get_current_weather(location: str) -> dict[str, Any]:
        """Get current weather conditions for a city or postal code.

        Args:
            location: Global city/place name or postal code, preferably with state or country.

        Returns:
            A status envelope containing the resolved location, local observation time,
            conditions, temperature, apparent temperature, humidity, precipitation, and wind.
        """
        return call(weather.get_current_weather, location)

    @server.tool
    def get_forecast(location: str, days: int = 7) -> dict[str, Any]:
        """Get a normalized daily weather forecast.

        Args:
            location: Global city/place name or postal code, preferably with state or country.
            days: Number of local forecast days to return, from 1 through 16.

        Returns:
            A status envelope with daily conditions, high/low temperatures, precipitation
            probability and amount, and maximum wind speed in labeled US customary units.
        """
        return call(weather.get_forecast, location, days)

    @server.tool
    def get_weather_recommendation(location: str, date: str) -> dict[str, Any]:
        """Get explainable rule-based weather recommendations for one date.

        The tool recommends an umbrella at 40% precipitation probability or 0.05 inch,
        a jacket below a 55°F low or 65°F high, heat caution at a 90°F high, and wind
        caution at 25 mph. It is general planning guidance, not a safety warning service.

        Args:
            location: Global city/place name or postal code, preferably with state or country.
            date: Local forecast date in YYYY-MM-DD form within the next 16 days.

        Returns:
            A status envelope with Boolean recommendations, triggering measurements,
            plain-language reasons, and the underlying daily forecast.
        """
        return call(weather.get_weather_recommendation, location, date)

    @server.tool
    def compare_weather(locations: list[str], date: str) -> dict[str, Any]:
        """Compare weather for two through five locations on the same date.

        Args:
            locations: Two through five global city/place names or postal codes.
            date: Local forecast date in YYYY-MM-DD form within the next 16 days.

        Returns:
            A success or partial envelope with forecasts and rankings for warmth,
            precipitation risk, and wind, plus clean per-location errors when applicable.
        """
        return call(weather.compare_weather, locations, date)

    return server


mcp = build_server()


if __name__ == "__main__":
    port = int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", "8000")))
    mcp.run(transport="http", host="0.0.0.0", port=port)
