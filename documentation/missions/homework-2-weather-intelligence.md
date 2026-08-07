# Mission: Build Weather Intelligence with Lakebase Vector Search

## Why

Be able to build and explain the Day 2 context-engineering pipeline without depending on the
lab's unreliable Spark/JDBC Lakebase write path: harvest unstructured text, preserve provenance,
embed chunks, and retrieve context with `pgvector`.

## Success looks like

- Resolve US city names or coordinates and harvest NWS forecast and active-alert narratives.
- Idempotently persist normalized documents in an isolated Lakebase schema.
- Chunk and embed current documents with 384-dimension MiniLM vectors using plain Python and
  `psycopg2`, casting directly to `vector` during the insert.
- Search those vectors through a deployed Flask endpoint and return ranked, attributable chunks.
- Preserve tested source, DDL, deployment evidence, and a credential-free submission archive.

## Constraints

- Reuse the existing Databricks App resource so the three-app Free Edition quota still leaves a
  slot for the capstone.
- Preserve the graded Day 1 source and submission unchanged.
- Use the existing `database/lakebase-url` secret for both app and embedding-job writes.
- Respect Nominatim's identification, caching, attribution, and one-request-per-second rules.
- No Spark/JDBC writes, no post-write array cast, and no credentials or model artifacts in Git.

## Out of scope

- LLM-generated weather summaries or other RAG generation.
- Scheduled refresh, multiple weather-text providers, and index benchmarking.
- A frontend beyond REST discovery and health endpoints.

## Outcome

- **Graded 100/100 on 2026-08-07:** Harvest 25/25, Vectorize 30/30, Retrieve 30/30, and
  Documentation 15/15.
- The grader confirmed direct `psycopg2` vector writes, genuine cosine semantic search, and one
  lazily cached embedding model, with no critical flags.
- Optional future refinements are a sentence-aware chunker and an `updated_at` name for the
  embedding timestamp that changes during upsert. They are not required corrections, so the
  graded implementation and submission archive remain frozen.
