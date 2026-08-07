from contextlib import contextmanager

from weather_app.repository import EmbeddingRecord, WeatherRepository
from weather_app.weather_client import WeatherDocument


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, params=None):
        self.executions.append((sql, params))

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1


def connection_factory(connection):
    @contextmanager
    def factory():
        yield connection

    return factory


def test_replace_embeddings_deletes_stale_chunks_and_inserts_directly_as_vectors():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    batch_calls = []

    def batch_insert(cursor_arg, sql, data, **kwargs):
        batch_calls.append((cursor_arg, sql, data, kwargs))

    repository = WeatherRepository(
        connection_factory=connection_factory(connection),
        batch_insert=batch_insert,
    )
    record = EmbeddingRecord(
        document_id="doc-1",
        chunk_index=0,
        chunk_text="Flooding is possible.",
        content_hash="abc123",
        embedding=[0.25] * 384,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
    )

    inserted = repository.replace_embeddings([record])

    assert inserted == 1
    assert "DELETE FROM weather_hw2.weather_embeddings" in cursor.executions[0][0]
    assert cursor.executions[0][1] == (["doc-1"], record.model_name)
    assert "%s::vector" in batch_calls[0][3]["template"]
    assert batch_calls[0][2][0][5].startswith("[")
    assert connection.commits == 1


def test_initialize_schema_and_document_upsert_preserve_the_database_contract():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    batch_calls = []

    def batch_insert(_cursor, sql, data, **kwargs):
        batch_calls.append((sql, data, kwargs))

    repository = WeatherRepository(
        connection_factory=connection_factory(connection),
        batch_insert=batch_insert,
    )
    document = WeatherDocument(
        id="doc-1",
        location="Chicago, IL",
        latitude=41.8781,
        longitude=-87.6298,
        source_type="forecast",
        headline="Tonight",
        narrative_text="Heavy rain is possible.",
        issued_at=None,
        effective_at=None,
        content_hash="a" * 64,
        payload={"source_url": "https://api.weather.gov/gridpoints/LOT/75,73/forecast"},
    )

    repository.initialize_schema()
    upserted = repository.upsert_documents([document])

    schema_sql = cursor.executions[0][0]
    assert "embedding VECTOR(384) NOT NULL" in schema_sql
    assert "REFERENCES weather_hw2.weather_documents(id) ON DELETE CASCADE" in schema_sql
    assert "USING hnsw (embedding vector_cosine_ops)" in schema_sql
    assert "ON CONFLICT (id) DO UPDATE" in batch_calls[0][0]
    assert batch_calls[0][2]["template"].endswith("%s::jsonb)")
    assert upserted == 1


def test_search_uses_cosine_distance_and_returns_empty_or_ranked_rows():
    rows = [
        {
            "document_id": "doc-1",
            "location": "Chicago, IL",
            "source_type": "alert",
            "headline": "Flood Warning",
            "chunk_text": "Move to higher ground.",
            "issued_at": None,
            "effective_at": None,
            "similarity": 0.91,
        }
    ]
    cursor = FakeCursor(rows)
    repository = WeatherRepository(connection_factory=connection_factory(FakeConnection(cursor)))

    matches = repository.search([0.5] * 384, top_k=5)

    assert matches == rows
    sql, params = cursor.executions[0]
    assert "1 - (e.embedding <=> %s::vector) AS similarity" in sql
    assert "ORDER BY e.embedding <=> %s::vector" in sql
    assert params[0] == params[2]
    assert params[1] == "sentence-transformers/all-MiniLM-L6-v2"
    assert params[3] == 5
