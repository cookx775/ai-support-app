from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    script_path = locals().get("__file__") or locals().get("filename")
    if script_path is None:
        raise RuntimeError("Unable to determine the Homework 2 application path")
    sys.path.insert(0, str(Path(script_path).resolve().parents[1]))

from weather_app.db import get_connection


def collect_schema_evidence(connection_factory: Any = get_connection) -> dict[str, Any]:
    with connection_factory() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    (SELECT count(*) FROM weather_hw2.weather_documents) AS documents,
                    (SELECT count(*) FROM weather_hw2.weather_embeddings) AS embeddings,
                    (
                        SELECT format_type(attribute.atttypid, attribute.atttypmod)
                        FROM pg_attribute AS attribute
                        WHERE attribute.attrelid =
                            'weather_hw2.weather_embeddings'::regclass
                          AND attribute.attname = 'embedding'
                          AND NOT attribute.attisdropped
                    ) AS vector_type,
                    EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'weather_hw2'
                          AND tablename = 'weather_embeddings'
                          AND indexdef ILIKE '%USING hnsw%'
                          AND indexdef ILIKE '%vector_cosine_ops%'
                    ) AS hnsw_cosine_index,
                    EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conrelid = 'weather_hw2.weather_embeddings'::regclass
                          AND confrelid = 'weather_hw2.weather_documents'::regclass
                          AND contype = 'f'
                    ) AS document_foreign_key
            """
        )
        row = cursor.fetchone()
    return dict(row)


def main() -> None:
    print(json.dumps(collect_schema_evidence(), sort_keys=True))


if __name__ == "__main__":
    main()
