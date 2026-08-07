from __future__ import annotations

import os
from collections.abc import Sequence
from functools import lru_cache
from typing import Any, Optional

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100


class EmbeddingDimensionError(ValueError):
    """Raised when an encoder does not emit the schema's vector dimension."""


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")
    if not isinstance(text, str) or not text.strip():
        return []

    step = chunk_size - chunk_overlap
    chunks = []
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    cache_dir = os.environ.get("HF_HOME", "/tmp/.cache/huggingface")
    os.environ.setdefault("HF_HOME", cache_dir)
    os.environ.setdefault("TRANSFORMERS_CACHE", cache_dir)
    os.environ.setdefault("HF_HUB_CACHE", cache_dir)
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME, cache_folder=cache_dir)


class EmbeddingService:
    def __init__(self, encoder: Optional[Any] = None) -> None:
        self._encoder = encoder

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        encoder = self._encoder or get_embedding_model()
        encoded = encoder.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        vectors = [[float(value) for value in vector] for vector in encoded]
        invalid = next(
            (len(vector) for vector in vectors if len(vector) != EMBEDDING_DIMENSION), None
        )
        if invalid is not None:
            raise EmbeddingDimensionError(
                f"Expected {EMBEDDING_DIMENSION}-dimensional embeddings, received {invalid}"
            )
        return vectors

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
