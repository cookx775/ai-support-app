from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    # Databricks Git-sourced Python tasks execute the file through ``exec`` and
    # expose its path as ``filename`` without defining ``__file__``.
    running_as_databricks_task = "__file__" not in locals() and "filename" in locals()
    script_path = locals().get("__file__") or locals().get("filename")
    if script_path is None:
        raise RuntimeError("Unable to determine the Homework 2 application path")
    sys.path.insert(0, str(Path(script_path).resolve().parents[1]))

    if running_as_databricks_task:
        # The Databricks serverless image includes a native psycopg2 build that
        # can abort the Python kernel when an overlay wheel is installed on top
        # of it. Remove both distributions and reinstall one clean binary wheel
        # before any weather_app module imports psycopg2.
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "psycopg2", "psycopg2-binary"],
            check=False,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "psycopg2-binary>=2.9.9,<3",
            ],
            check=True,
        )

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
