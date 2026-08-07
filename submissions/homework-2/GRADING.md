# Homework 2 Grading Record

## Result

- **Score:** 100/100
- **Recorded:** 2026-08-07
- **Harvest:** 25/25
- **Vectorize:** 30/30
- **Retrieve:** 30/30
- **Documentation:** 15/15

## Confirmed strengths

- NWS forecast and alert narratives are harvested with validated location resolution,
  normalization, retry behavior, stable document identities, and partial-failure handling.
- Documents and embeddings are written directly through `psycopg2`; Spark JDBC is absent from
  the embedding write path.
- MiniLM vectors are normalized, 384-dimensional, inserted with direct `%s::vector` casts, and
  searched with pgvector cosine distance.
- The embedding model is loaded lazily and cached rather than recreated for each request.
- Request validation, empty results, clamping, stale-vector replacement, schema constraints,
  HNSW indexing, and deployment procedures are covered by tests and documentation.

## Critical flags

- Spark JDBC used for embedding writes: **No**
- Retrieval is real semantic search rather than keyword/`LIKE`: **Yes**
- Model loaded once rather than per request: **Yes**

## Future polish

The grader suggested two optional improvements, neither of which reduced the score:

1. Replace fixed character-window chunking with sentence-aware chunking.
2. Rename `weather_embeddings.created_at` to `updated_at`, since an upsert refreshes the value.

These are recorded for a future version. The graded source, schema, and submission ZIP remain
unchanged to preserve the submitted artifact.
