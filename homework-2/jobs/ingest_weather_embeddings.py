from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from weather_app.embeddings import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MODEL_NAME,
    EmbeddingService,
    chunk_text,
)
from weather_app.repository import EmbeddingRecord, WeatherRepository


def run_ingestion(
    repository: Any,
    embedding_service: Any,
    document_limit: Optional[int] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict[str, int]:
    documents = repository.get_documents_to_embed(limit=document_limit)
    chunk_metadata = []
    for document in documents:
        for chunk_index, text in enumerate(
            chunk_text(
                document["narrative_text"],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        ):
            chunk_metadata.append(
                (
                    document["id"],
                    chunk_index,
                    text,
                    document["content_hash"],
                )
            )

    vectors = embedding_service.embed_texts([metadata[2] for metadata in chunk_metadata])
    records = [
        EmbeddingRecord(
            document_id=metadata[0],
            chunk_index=metadata[1],
            chunk_text=metadata[2],
            content_hash=metadata[3],
            embedding=vector,
            model_name=MODEL_NAME,
        )
        for metadata, vector in zip(chunk_metadata, vectors)
    ]
    inserted = repository.replace_embeddings(records)
    return {"documents": len(documents), "chunks": len(records), "inserted": inserted}


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed unprocessed weather documents in Lakebase")
    parser.add_argument("--limit", type=int, default=None, help="Maximum documents to process")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args()

    repository = WeatherRepository()
    repository.initialize_schema()
    result = run_ingestion(
        repository=repository,
        embedding_service=EmbeddingService(),
        document_limit=args.limit,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
