from jobs.ingest_weather_embeddings import run_ingestion


class FakeRepository:
    def __init__(self):
        self.replaced = []

    def get_documents_to_embed(self, limit=None):
        assert limit == 10
        return [
            {"id": "doc-1", "narrative_text": "abcdefghij", "content_hash": "a" * 64},
            {"id": "doc-2", "narrative_text": "storm", "content_hash": "b" * 64},
        ]

    def replace_embeddings(self, records):
        self.replaced.extend(records)
        return len(records)


class FakeEmbeddingService:
    def embed_texts(self, texts):
        return [[float(index)] * 384 for index, _text in enumerate(texts)]


def test_ingestion_job_chunks_embeds_and_replaces_only_current_documents():
    repository = FakeRepository()

    result = run_ingestion(
        repository=repository,
        embedding_service=FakeEmbeddingService(),
        document_limit=10,
        chunk_size=6,
        chunk_overlap=2,
    )

    assert result == {"documents": 2, "chunks": 3, "inserted": 3}
    assert [record.chunk_text for record in repository.replaced] == [
        "abcdef",
        "efghij",
        "storm",
    ]
    assert repository.replaced[0].content_hash == "a" * 64
