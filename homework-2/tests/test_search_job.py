from decimal import Decimal

from jobs.search_weather import run_search


class FakeEmbeddingService:
    def embed_query(self, query):
        assert query == "flood risk"
        return [0.5] * 384


class FakeRepository:
    def search(self, vector, top_k):
        assert len(vector) == 384
        assert top_k == 3
        return [{"location_label": "Chicago, IL", "similarity": Decimal("0.91")}]


def test_run_search_embeds_query_and_serializes_similarity():
    result = run_search(
        FakeRepository(),
        FakeEmbeddingService(),
        " flood risk ",
        top_k=3,
    )

    assert result == {
        "query": "flood risk",
        "top_k": 3,
        "matches": [{"location_label": "Chicago, IL", "similarity": 0.91}],
    }
