from __future__ import annotations

import pytest
import requests
from open_meteo import OpenMeteoClient, WeatherServiceError


class StubResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class CurrentWeatherSession:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "geocoding-api" in url:
            return StubResponse(
                {
                    "results": [
                        {
                            "name": "Chicago",
                            "admin1": "Illinois",
                            "country": "United States",
                            "country_code": "US",
                            "latitude": 41.85,
                            "longitude": -87.65,
                            "timezone": "America/Chicago",
                        }
                    ]
                }
            )
        return StubResponse(
            {
                "latitude": 41.85,
                "longitude": -87.65,
                "timezone": "America/Chicago",
                "current_units": {
                    "temperature_2m": "°F",
                    "apparent_temperature": "°F",
                    "relative_humidity_2m": "%",
                    "precipitation": "inch",
                    "wind_speed_10m": "mp/h",
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


def test_current_weather_returns_canonical_location_conditions_and_labeled_units():
    session = CurrentWeatherSession()
    client = OpenMeteoClient(session=session, sleeper=lambda _seconds: None)

    result = client.get_current_weather("Chicago, IL")

    assert result == {
        "status": "success",
        "location": {
            "requested": "Chicago, IL",
            "name": "Chicago, Illinois, United States",
            "country_code": "US",
            "latitude": 41.85,
            "longitude": -87.65,
            "timezone": "America/Chicago",
        },
        "observed_at": "2026-08-08T13:15",
        "conditions": "Partly cloudy",
        "temperature": {"value": 75.3, "unit": "°F"},
        "apparent_temperature": {"value": 83.6, "unit": "°F"},
        "relative_humidity": {"value": 85, "unit": "%"},
        "precipitation": {"value": 0.0, "unit": "inch"},
        "wind_speed": {"value": 8.2, "unit": "mph"},
        "source": "Open-Meteo",
    }

    repeated = client.get_current_weather("Chicago, IL")
    assert repeated["location"] == result["location"]
    geocoding_calls = [call for call in session.calls if "geocoding-api" in call[0]]
    assert len(geocoding_calls) == 1


class DailyForecastSession:
    def get(self, url, **kwargs):
        query = kwargs["params"].get("name")
        if "geocoding-api" in url:
            city = "Austin" if query and "Austin" in query else "Chicago"
            state = "Texas" if city == "Austin" else "Illinois"
            latitude = 30.27 if city == "Austin" else 41.85
            longitude = -97.74 if city == "Austin" else -87.65
            timezone = "America/Chicago"
            return StubResponse(
                {
                    "results": [
                        {
                            "name": city,
                            "admin1": state,
                            "country": "United States",
                            "country_code": "US",
                            "latitude": latitude,
                            "longitude": longitude,
                            "timezone": timezone,
                        }
                    ]
                }
            )
        return StubResponse(
            {
                "timezone": "America/Chicago",
                "daily_units": {
                    "temperature_2m_max": "°F",
                    "temperature_2m_min": "°F",
                    "precipitation_probability_max": "%",
                    "precipitation_sum": "inch",
                    "wind_speed_10m_max": "mp/h",
                },
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


class CompareForecastSession(DailyForecastSession):
    def get(self, url, **kwargs):
        params = kwargs["params"]
        if "geocoding-api" in url and params.get("name") == "Missing":
            return StubResponse({"results": []})
        response = super().get(url, **kwargs)
        if "geocoding-api" not in url and params["latitude"] == 30.27:
            payload = response.json()
            payload["daily"]["temperature_2m_max"] = [90.0, 88.0, 86.0]
            payload["daily"]["temperature_2m_min"] = [72.0, 70.0, 69.0]
            payload["daily"]["precipitation_probability_max"] = [10, 15, 20]
            payload["daily"]["precipitation_sum"] = [0.0, 0.0, 0.01]
            payload["daily"]["wind_speed_10m_max"] = [7.0, 9.0, 11.0]
        return response


def test_forecast_returns_requested_number_of_normalized_local_days():
    client = OpenMeteoClient(session=DailyForecastSession(), sleeper=lambda _seconds: None)

    result = client.get_forecast("Chicago, IL", days=2)

    assert result["status"] == "success"
    assert result["location"]["name"] == "Chicago, Illinois, United States"
    assert result["timezone"] == "America/Chicago"
    assert result["forecast_days"] == 2
    assert result["days"] == [
        {
            "date": "2026-08-08",
            "conditions": "Partly cloudy",
            "temperature_high": {"value": 76.8, "unit": "°F"},
            "temperature_low": {"value": 67.4, "unit": "°F"},
            "precipitation_probability": {"value": 5, "unit": "%"},
            "precipitation": {"value": 0.0, "unit": "inch"},
            "wind_speed_max": {"value": 8.6, "unit": "mph"},
        },
        {
            "date": "2026-08-09",
            "conditions": "Slight rain",
            "temperature_high": {"value": 64.0, "unit": "°F"},
            "temperature_low": {"value": 54.0, "unit": "°F"},
            "precipitation_probability": {"value": 40, "unit": "%"},
            "precipitation": {"value": 0.05, "unit": "inch"},
            "wind_speed_max": {"value": 25.0, "unit": "mph"},
        },
    ]
    assert result["source"] == "Open-Meteo"


def test_recommendation_applies_documented_thresholds_and_explains_each_decision():
    client = OpenMeteoClient(session=DailyForecastSession(), sleeper=lambda _seconds: None)

    result = client.get_weather_recommendation("Chicago, IL", "2026-08-09")

    assert result["status"] == "success"
    assert result["date"] == "2026-08-09"
    assert result["recommendations"] == {
        "umbrella_needed": True,
        "jacket_recommended": True,
        "heat_caution": False,
        "wind_caution": True,
    }
    assert result["summary"] == "Bring an umbrella and a jacket; use caution in strong winds."
    assert result["reasons"] == [
        "Umbrella recommended: precipitation probability is 40% and forecast amount is 0.05 inch.",
        "Jacket recommended: forecast high is 64.0°F and low is 54.0°F.",
        "Wind caution: maximum wind is 25.0 mph.",
    ]
    assert result["forecast"]["conditions"] == "Slight rain"


def test_compare_weather_ranks_successes_and_preserves_a_failed_location():
    client = OpenMeteoClient(session=CompareForecastSession(), sleeper=lambda _seconds: None)

    result = client.compare_weather(
        ["Chicago, IL", "Austin, TX", "Missing"], "2026-08-09"
    )

    assert result["status"] == "partial"
    assert result["date"] == "2026-08-09"
    assert [item["location"]["name"] for item in result["comparisons"]] == [
        "Chicago, Illinois, United States",
        "Austin, Texas, United States",
    ]
    assert result["rankings"] == {
        "warmest_first": [
            "Austin, Texas, United States",
            "Chicago, Illinois, United States",
        ],
        "lowest_precipitation_risk_first": [
            "Austin, Texas, United States",
            "Chicago, Illinois, United States",
        ],
        "least_windy_first": [
            "Austin, Texas, United States",
            "Chicago, Illinois, United States",
        ],
    }
    assert result["errors"] == [
        {"location": "Missing", "message": "No location found for 'Missing'"}
    ]


class ThresholdSession(DailyForecastSession):
    def __init__(self, *, probability=0, precipitation=0.0, high=70.0, low=60.0, wind=10.0):
        self.values = {
            "precipitation_probability_max": [probability],
            "precipitation_sum": [precipitation],
            "temperature_2m_max": [high],
            "temperature_2m_min": [low],
            "wind_speed_10m_max": [wind],
        }

    def get(self, url, **kwargs):
        response = super().get(url, **kwargs)
        if "geocoding-api" not in url:
            payload = response.json()
            payload["daily"]["time"] = ["2026-08-09"]
            payload["daily"]["weather_code"] = [0]
            payload["daily"].update(self.values)
        return response


@pytest.mark.parametrize(
    ("field", "values", "flag", "expected"),
    [
        ("probability", [39, 40, 41], "umbrella_needed", [False, True, True]),
        ("precipitation", [0.04, 0.05, 0.06], "umbrella_needed", [False, True, True]),
        ("low", [54.9, 55.0, 55.1], "jacket_recommended", [True, False, False]),
        ("high", [64.9, 65.0, 65.1], "jacket_recommended", [True, False, False]),
        ("high", [89.9, 90.0, 90.1], "heat_caution", [False, True, True]),
        ("wind", [24.9, 25.0, 25.1], "wind_caution", [False, True, True]),
    ],
)
def test_recommendation_threshold_boundaries(field, values, flag, expected):
    actual = []
    for value in values:
        client = OpenMeteoClient(
            session=ThresholdSession(**{field: value}), sleeper=lambda _seconds: None
        )
        result = client.get_weather_recommendation("Chicago, IL", "2026-08-09")
        actual.append(result["recommendations"][flag])
    assert actual == expected


class FlakySession(CurrentWeatherSession):
    def __init__(self):
        super().__init__()
        self.attempts = 0

    def get(self, url, **kwargs):
        if "geocoding-api" in url:
            self.attempts += 1
            if self.attempts < 3:
                raise requests.ConnectionError("temporary outage")
        return super().get(url, **kwargs)


def test_transient_api_failures_are_retried_with_backoff():
    session = FlakySession()
    sleeps = []
    client = OpenMeteoClient(session=session, sleeper=sleeps.append)

    assert client.get_current_weather("Chicago, IL")["status"] == "success"
    assert session.attempts == 3
    assert sleeps == [0.5, 1.0]


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (lambda client: client.get_current_weather(""), "Location must be a non-empty"),
        (lambda client: client.get_forecast("Chicago, IL", 0), "integer from 1 through 16"),
        (
            lambda client: client.get_weather_recommendation("Chicago, IL", "tomorrow"),
            "YYYY-MM-DD",
        ),
        (
            lambda client: client.get_weather_recommendation("Chicago, IL", "2027-01-01"),
            "outside the available forecast horizon",
        ),
        (
            lambda client: client.compare_weather(["Chicago, IL"], "2026-08-09"),
            "two through five locations",
        ),
    ],
)
def test_invalid_public_inputs_return_specific_adapter_errors(operation, message):
    client = OpenMeteoClient(session=DailyForecastSession(), sleeper=lambda _seconds: None)

    with pytest.raises(WeatherServiceError, match=message):
        operation(client)


class MisalignedDailySession(DailyForecastSession):
    def get(self, url, **kwargs):
        response = super().get(url, **kwargs)
        if "geocoding-api" not in url:
            response.json()["daily"]["wind_speed_10m_max"] = [8.6]
        return response


def test_misaligned_daily_arrays_are_reported_as_an_upstream_error():
    client = OpenMeteoClient(session=MisalignedDailySession(), sleeper=lambda _seconds: None)

    with pytest.raises(WeatherServiceError, match="incomplete daily forecast"):
        client.get_forecast("Chicago, IL", 3)
