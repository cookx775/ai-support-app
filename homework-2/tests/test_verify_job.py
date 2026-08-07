from jobs.verify_lakebase_schema import collect_schema_evidence


class FakeCursor:
    def __init__(self):
        self.sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql):
        self.sql = sql

    def fetchone(self):
        return {
            "documents": 28,
            "embeddings": 28,
            "vector_type": "vector(384)",
            "hnsw_cosine_index": True,
            "document_foreign_key": True,
        }


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        return self.fake_cursor


def test_collect_schema_evidence_checks_required_database_objects():
    connection = FakeConnection()

    result = collect_schema_evidence(lambda: connection)

    assert result == {
        "documents": 28,
        "embeddings": 28,
        "vector_type": "vector(384)",
        "hnsw_cosine_index": True,
        "document_foreign_key": True,
    }
    assert "USING hnsw" in connection.fake_cursor.sql
    assert "vector_cosine_ops" in connection.fake_cursor.sql
    assert "contype = 'f'" in connection.fake_cursor.sql
