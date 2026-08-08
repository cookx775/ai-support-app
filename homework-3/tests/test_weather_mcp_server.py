from __future__ import annotations

import asyncio

from fastmcp import Client
from open_meteo import OpenMeteoClient
from weather_mcp_server import build_server


class StubResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class ProtocolWeatherSession:
    def get(self, url, **kwargs):
        params = kwargs["params"]
        if "geocoding-api" in url:
            city = "Austin" if "Austin" in params["name"] else "Chicago"
            return StubResponse(
                {
                    "results": [
                        {
                            "name": city,
                            "admin1": "Texas" if city == "Austin" else "Illinois",
                            "country": "United States",
                            "country_code": "US",
                            "latitude": 30.27 if city == "Austin" else 41.85,
                            "longitude": -97.74 if city == "Austin" else -87.65,
                            "timezone": "America/Chicago",
                        }
                    ]
                }
            )
        if "current" in params:
            return StubResponse(
                {
                    "current_units": {
                        "temperature_2m": "°F",
                        "apparent_temperature": "°F",
                        "relative_humidity_2m": "%",
                        "precipitation": "inch",
                    },
                    "current": {
                        "time": "2026-08-08T13:15",
                        "temperature_2m": 75.3,
                        "apparent_temperature": 83.6,
                        "relative_humidity_2m": 85,
                        "precipitation": 0.0,
                        "weather_code": 2,
                        "wind_speed_10m": 8.2,
                    },
                }
            )
        return StubResponse(
            {
                "timezone": "America/Chicago",
                "daily": {
                    "time": ["2026-08-08", "2026-08-09", "2026-08-10"],
                    "weather_code": [2, 61, 95],
                    "temperature_2m_max": [76.8, 64.0, 92.0],
                    "temperature_2m_min": [67.4, 54.0, 70.0],
                    "precipitation_probability_max": [5, 40, 80],
                    "precipitation_sum": [0.0, 0.05, 0.4],
                    "wind_speed_10m_max": [8.6, 25.0, 30.0],
                },
            }
        )


def test_mcp_protocol_discovers_and_calls_all_weather_tools_with_clean_errors():
    adapter = OpenMeteoClient(session=ProtocolWeatherSession(), sleeper=lambda _seconds: None)
    server = build_server(adapter)

    async def exercise_tools():
        async with Client(server) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools] == [
                "get_current_weather",
                "get_forecast",
                "get_weather_recommendation",
                "compare_weather",
            ]

            current = await client.call_tool("get_current_weather", {"location": "Chicago, IL"})
            forecast = await client.call_tool(
                "get_forecast", {"location": "Chicago, IL", "days": 2}
            )
            advice = await client.call_tool(
                "get_weather_recommendation",
                {"location": "Chicago, IL", "date": "2026-08-09"},
            )
            comparison = await client.call_tool(
                "compare_weather",
                {
                    "locations": ["Chicago, IL", "Austin, TX"],
                    "date": "2026-08-09",
                },
            )
            invalid = await client.call_tool(
                "get_forecast", {"location": "Chicago, IL", "days": 0}
            )

            assert current.data["status"] == "success"
            assert forecast.data["forecast_days"] == 2
            assert advice.data["recommendations"]["umbrella_needed"] is True
            assert comparison.data["status"] == "success"
            assert invalid.data == {
                "status": "error",
                "error": {
                    "type": "weather_service_error",
                    "message": "Forecast days must be an integer from 1 through 16",
                },
            }

    asyncio.run(exercise_tools())
