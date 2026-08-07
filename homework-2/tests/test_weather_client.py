import requests
from weather_app.weather_client import ResolvedLocation, WeatherClient, WeatherClientError


class StubResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class StubSession:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "nominatim.openstreetmap.org" in url:
            return StubResponse([{"lat": "41.8781", "lon": "-87.6298"}])
        if "/points/" in url:
            return StubResponse(
                {
                    "properties": {
                        "forecast": "https://api.weather.gov/gridpoints/LOT/75,73/forecast",
                    }
                }
            )
        if "/gridpoints/" in url:
            return StubResponse(
                {
                    "properties": {
                        "generatedAt": "2026-08-06T18:00:00+00:00",
                        "periods": [
                            {
                                "name": "Tonight",
                                "startTime": "2026-08-06T19:00:00-05:00",
                                "detailedForecast": "Heavy rain with a chance of flooding.",
                            },
                            {"name": "Empty", "detailedForecast": "   "},
                        ],
                    }
                }
            )
        if "/alerts/active" in url:
            return StubResponse(
                {
                    "features": [
                        {
                            "id": "https://api.weather.gov/alerts/alert-1",
                            "properties": {
                                "event": "Flash Flood Warning",
                                "headline": "Flash Flood Warning issued for Cook County",
                                "description": "Flooding is occurring near rivers.",
                                "instruction": "Move to higher ground.",
                                "sent": "2026-08-06T18:15:00-05:00",
                                "effective": "2026-08-06T18:15:00-05:00",
                            },
                        },
                        {"id": "empty-alert", "properties": {"description": ""}},
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")


def test_fetch_documents_normalizes_forecast_and_alert_records():
    session = StubSession()
    client = WeatherClient(session=session, sleeper=lambda _seconds: None)
    location = ResolvedLocation("Chicago, IL", 41.8781, -87.6298)

    documents = client.fetch_documents(location, limit=50)

    assert [document.source_type for document in documents] == ["alert", "forecast"]
    assert documents[0].id == "https://api.weather.gov/alerts/alert-1"
    assert documents[0].headline == "Flash Flood Warning issued for Cook County"
    assert documents[0].narrative_text == (
        "Flooding is occurring near rivers.\n\nMove to higher ground."
    )
    assert documents[0].payload["source_url"].endswith("/alerts/active")
    assert documents[1].headline == "Tonight"
    assert documents[1].id.startswith("forecast:")
    assert len(documents[1].content_hash) == 64

    repeated_documents = client.fetch_documents(location, limit=50)
    assert repeated_documents[1].id == documents[1].id


def test_resolve_location_accepts_city_object_and_coordinate_pair_and_caches_city():
    session = StubSession()
    client = WeatherClient(session=session, sleeper=lambda _seconds: None)

    city = client.resolve_location("Chicago, IL")
    cached_city = client.resolve_location("Chicago, IL")
    coordinate_object = client.resolve_location(
        {"lat": 30.2672, "lon": -97.7431, "label": "Austin, TX"}
    )
    coordinate_pair = client.resolve_location([39.7392, -104.9903])

    assert city == ResolvedLocation("Chicago, IL", 41.8781, -87.6298)
    assert cached_city == city
    assert coordinate_object == ResolvedLocation("Austin, TX", 30.2672, -97.7431)
    assert coordinate_pair == ResolvedLocation("39.7392,-104.9903", 39.7392, -104.9903)
    geocoder_calls = [call for call in session.calls if "nominatim" in call[0]]
    assert len(geocoder_calls) == 1
    assert geocoder_calls[0][1]["params"]["countrycodes"] == "us"


class FlakySession(StubSession):
    def __init__(self):
        super().__init__()
        self.point_attempts = 0

    def get(self, url, **kwargs):
        if "/points/" in url:
            self.point_attempts += 1
            if self.point_attempts < 3:
                raise requests.ConnectionError("temporary NWS failure")
        return super().get(url, **kwargs)


def test_fetch_documents_retries_transient_nws_failures():
    session = FlakySession()
    sleeps = []
    client = WeatherClient(session=session, sleeper=sleeps.append, max_attempts=3)

    documents = client.fetch_documents(ResolvedLocation("Chicago, IL", 41.8781, -87.6298))

    assert len(documents) == 2
    assert session.point_attempts == 3
    assert sleeps == [0.5, 1.0]


class InvalidJsonSession:
    def get(self, _url, **_kwargs):
        return StubResponse([])


def test_fetch_documents_wraps_malformed_nws_payloads_as_upstream_errors():
    client = WeatherClient(session=InvalidJsonSession(), sleeper=lambda _seconds: None)

    try:
        client.fetch_documents(ResolvedLocation("Chicago, IL", 41.8781, -87.6298))
    except WeatherClientError as exc:
        assert "Unable to fetch NWS data for Chicago, IL" in str(exc)
    else:
        raise AssertionError("Malformed NWS JSON should fail the location sync")
