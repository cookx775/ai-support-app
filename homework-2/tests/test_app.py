from weather_app.app import create_app
from weather_app.weather_client import (
    LocationValidationError,
    ResolvedLocation,
    WeatherClientError,
    WeatherDocument,
)


class FakeWeatherClient:
    def __init__(self):
        self.fetch_limits = []

    def resolve_location(self, value):
        if value == "Broken, IL":
            raise WeatherClientError("NWS unavailable")
        if value == "Invalid":
            raise LocationValidationError("Unknown location")
        return ResolvedLocation(str(value), 41.8781, -87.6298)

    def fetch_documents(self, location, limit):
        self.fetch_limits.append(limit)
        return [
            WeatherDocument(
                id="alert-1",
                location=location.label,
                latitude=location.latitude,
                longitude=location.longitude,
                source_type="alert",
                headline="Flood Warning",
                narrative_text="Move to higher ground.",
                issued_at=None,
                effective_at=None,
                content_hash="a" * 64,
                payload={"source_url": "https://api.weather.gov/alerts/active", "item": {}},
            )
        ]


class FakeRepository:
    def __init__(self, matches=None, fail_writes=False):
        self.documents = []
        self.search_calls = []
        self.matches = matches or []
        self.fail_writes = fail_writes

    def initialize_schema(self):
        raise AssertionError("Tests must not initialize Lakebase")

    def upsert_documents(self, documents):
        if self.fail_writes:
            raise RuntimeError("database unavailable")
        self.documents.extend(documents)
        return len(documents)

    def search(self, vector, top_k):
        self.search_calls.append((vector, top_k))
        return self.matches


class FakeEmbeddings:
    def __init__(self):
        self.queries = []

    def embed_query(self, query):
        self.queries.append(query)
        return [0.1] * 384


def build_client(repository=None, weather_client=None, embeddings=None):
    app = create_app(
        repository=repository or FakeRepository(),
        weather_client=weather_client or FakeWeatherClient(),
        embeddings=embeddings or FakeEmbeddings(),
        initialize_schema=False,
    )
    app.config.update(TESTING=True)
    return app.test_client()


def test_weather_sync_clamps_limit_and_returns_partial_success_details():
    weather_client = FakeWeatherClient()
    repository = FakeRepository()
    client = build_client(repository=repository, weather_client=weather_client)

    response = client.post(
        "/weather/sync",
        json={"locations": ["Chicago, IL", "Broken, IL"], "limit": 100},
    )

    assert response.status_code == 200
    assert response.json["synced"] == 1
    assert response.json["resolved_locations"][0]["label"] == "Chicago, IL"
    assert response.json["errors"] == [{"location": "Broken, IL", "error": "NWS unavailable"}]
    assert weather_client.fetch_limits == [50]


def test_weather_sync_returns_502_when_every_location_fails_upstream():
    client = build_client()

    response = client.post("/weather/sync", json={"locations": ["Broken, IL"]})

    assert response.status_code == 502
    assert response.json["synced"] == 0


def test_weather_sync_reserves_502_for_all_upstream_failures():
    client = build_client()

    mixed = client.post(
        "/weather/sync",
        json={"locations": ["Invalid", "Broken, IL"]},
    )
    database = build_client(repository=FakeRepository(fail_writes=True)).post(
        "/weather/sync",
        json={"locations": ["Chicago, IL"]},
    )

    assert mixed.status_code == 400
    assert database.status_code == 500


def test_weather_search_validates_query_and_clamps_top_k():
    repository = FakeRepository(
        matches=[
            {
                "document_id": "alert-1",
                "location": "Chicago, IL",
                "source_type": "alert",
                "headline": "Flood Warning",
                "chunk_text": "Move to higher ground.",
                "issued_at": None,
                "effective_at": None,
                "similarity": 0.91,
            }
        ]
    )
    embeddings = FakeEmbeddings()
    client = build_client(repository=repository, embeddings=embeddings)

    invalid = client.post("/weather/search", json={"query": "  "})
    response = client.post("/weather/search", json={"query": " flood risk ", "top_k": 99})

    assert invalid.status_code == 400
    assert response.status_code == 200
    assert response.json["matches"][0]["similarity"] == 0.91
    assert embeddings.queries == ["flood risk"]
    assert repository.search_calls[0][1] == 20


def test_weather_search_returns_an_empty_match_list_before_ingestion():
    client = build_client()

    response = client.post("/weather/search", json={"query": "river flooding"})

    assert response.status_code == 200
    assert response.json["matches"] == []
