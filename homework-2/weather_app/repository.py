from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from psycopg2.extras import execute_values

from weather_app.db import get_connection
from weather_app.weather_client import WeatherDocument

SCHEMA_NAME = "weather_hw2"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class EmbeddingRecord:
    document_id: str
    chunk_index: int
    chunk_text: str
    content_hash: str
    embedding: list[float]
    model_name: str = MODEL_NAME


class WeatherRepository:
    def __init__(
        self,
        connection_factory: Callable = get_connection,
        batch_insert: Callable = execute_values,
    ) -> None:
        self._connection_factory = connection_factory
        self._batch_insert = batch_insert

    def initialize_schema(self) -> None:
        schema_path = Path(__file__).parents[1] / "sql" / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        with self._connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()

    def upsert_documents(self, documents: Sequence[WeatherDocument]) -> int:
        if not documents:
            return 0
        values = [
            (
                document.id,
                document.location,
                document.latitude,
                document.longitude,
                document.source_type,
                document.headline,
                document.narrative_text,
                document.issued_at,
                document.effective_at,
                document.content_hash,
                json.dumps(document.payload),
            )
            for document in documents
        ]
        sql = f"""
            INSERT INTO {SCHEMA_NAME}.weather_documents (
                id, location, latitude, longitude, source_type, headline,
                narrative_text, issued_at, effective_at, content_hash, payload
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                location = EXCLUDED.location,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                source_type = EXCLUDED.source_type,
                headline = EXCLUDED.headline,
                narrative_text = EXCLUDED.narrative_text,
                issued_at = EXCLUDED.issued_at,
                effective_at = EXCLUDED.effective_at,
                content_hash = EXCLUDED.content_hash,
                payload = EXCLUDED.payload,
                synced_at = now()
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cursor:
                self._batch_insert(
                    cursor,
                    sql,
                    values,
                    template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",
                    page_size=100,
                )
            conn.commit()
        return len(documents)

    def get_documents_to_embed(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        params: list[Any] = [MODEL_NAME]
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT %s"
            params.append(max(1, int(limit)))
        sql = f"""
            SELECT d.id, d.narrative_text, d.content_hash
            FROM {SCHEMA_NAME}.weather_documents d
            WHERE NOT EXISTS (
                SELECT 1
                FROM {SCHEMA_NAME}.weather_embeddings e
                WHERE e.document_id = d.id
                  AND e.model_name = %s
                  AND e.content_hash = d.content_hash
            )
            ORDER BY d.synced_at, d.id
            {limit_clause}
        """
        return self._query(sql, tuple(params))

    def replace_embeddings(self, records: Sequence[EmbeddingRecord]) -> int:
        if not records:
            return 0
        model_names = {record.model_name for record in records}
        if len(model_names) != 1:
            raise ValueError("A replacement batch must use one embedding model")
        model_name = next(iter(model_names))
        document_ids = sorted({record.document_id for record in records})
        values = [
            (
                record.document_id,
                record.chunk_index,
                record.chunk_text,
                record.content_hash,
                record.model_name,
                _vector_literal(record.embedding),
            )
            for record in records
        ]
        sql = f"""
            INSERT INTO {SCHEMA_NAME}.weather_embeddings (
                document_id, chunk_index, chunk_text, content_hash, model_name, embedding
            ) VALUES %s
            ON CONFLICT (document_id, chunk_index, model_name) DO UPDATE SET
                chunk_text = EXCLUDED.chunk_text,
                content_hash = EXCLUDED.content_hash,
                embedding = EXCLUDED.embedding,
                created_at = now()
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {SCHEMA_NAME}.weather_embeddings "
                    "WHERE document_id = ANY(%s) AND model_name = %s",
                    (document_ids, model_name),
                )
                self._batch_insert(
                    cursor,
                    sql,
                    values,
                    template="(%s,%s,%s,%s,%s,%s::vector)",
                    page_size=100,
                )
            conn.commit()
        return len(records)

    def search(self, embedding: Sequence[float], top_k: int) -> list[dict[str, Any]]:
        vector = _vector_literal(embedding)
        sql = f"""
            SELECT
                d.id AS document_id,
                d.location,
                d.source_type,
                d.headline,
                e.chunk_text,
                d.issued_at,
                d.effective_at,
                1 - (e.embedding <=> %s::vector) AS similarity
            FROM {SCHEMA_NAME}.weather_embeddings e
            JOIN {SCHEMA_NAME}.weather_documents d ON d.id = e.document_id
            WHERE e.model_name = %s
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """
        return self._query(sql, (vector, MODEL_NAME, vector, max(1, min(int(top_k), 20))))

    def counts(self) -> dict[str, int]:
        rows = self._query(
            f"""
            SELECT
                (SELECT COUNT(*) FROM {SCHEMA_NAME}.weather_documents) AS documents,
                (SELECT COUNT(*) FROM {SCHEMA_NAME}.weather_embeddings) AS embeddings
            """
        )
        return rows[0] if rows else {"documents": 0, "embeddings": 0}

    def _query(self, sql: str, params: Optional[tuple] = None) -> list[dict[str, Any]]:
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def _vector_literal(values: Iterable[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"
