from dataclasses import dataclass

from jobs.sync_weather_documents import run_sync
from weather_app.weather_client import WeatherClientError


@dataclass
class ResolvedLocation:
    label: str
    latitude: float
    longitude: float


class FakeRepository:
    def __init__(self):
        self.initialized = False

    def initialize_schema(self):
        self.initialized = True

    def upsert_documents(self, documents):
        return len(documents)


class FakeWeatherClient:
    def resolve_location(self, location):
        if location == "Broken":
            raise WeatherClientError("unavailable")
        return ResolvedLocation(location, 41.0, -87.0)

    def fetch_documents(self, resolved, limit):
        return [{"id": f"{resolved.label}-{index}"} for index in range(min(limit, 2))]


def test_run_sync_returns_counts_and_partial_errors():
    repository = FakeRepository()

    result = run_sync(
        repository,
        FakeWeatherClient(),
        ["Chicago, IL", "Broken"],
        limit=2,
    )

    assert repository.initialized is True
    assert result["synced"] == 2
    assert result["resolved_locations"][0]["label"] == "Chicago, IL"
    assert result["errors"] == [{"location": "Broken", "error": "unavailable"}]
