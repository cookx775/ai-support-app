import pytest
from weather_app.embeddings import EmbeddingDimensionError, EmbeddingService, chunk_text


class StubEncoder:
    def __init__(self, dimensions=384):
        self.dimensions = dimensions
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return [[float(index) for index in range(self.dimensions)] for _text in texts]


def test_chunk_text_uses_an_overlapping_sliding_window():
    chunks = chunk_text("abcdefghij", chunk_size=6, chunk_overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_embedding_service_normalizes_and_enforces_384_dimensions():
    encoder = StubEncoder()
    service = EmbeddingService(encoder=encoder)

    vectors = service.embed_texts(["flood risk"])

    assert len(vectors[0]) == 384
    assert encoder.calls[0][1]["normalize_embeddings"] is True

    with pytest.raises(EmbeddingDimensionError):
        EmbeddingService(encoder=StubEncoder(dimensions=383)).embed_texts(["flood risk"])
