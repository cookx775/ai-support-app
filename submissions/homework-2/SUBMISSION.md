# Day 2 Homework Submission

## Deliverables

- **Databricks App URL:** https://ai-support-app-7474657586545240.aws.databricksapps.com
- **Complete upload archive:** `weather-intelligence-submission.zip`
- **Deployed service evidence:** `screenshots/deployed-app.png`
- **Semantic search evidence:** `screenshots/semantic-search.png`
- **Lakebase tables/vector evidence:** `screenshots/lakebase-vectors.png`

The evidence images transcribe the credential-free fields from the live Databricks deployment
and job-run pages. Exact run IDs are included so the results can be reopened in the workspace.

## Verification checklist

- [x] Local tests cover harvesting, normalization, chunking, vector insertion, retrieval, and API validation.
- [x] Embeddings are written by `psycopg2` with a direct `%s::vector` cast.
- [x] The schema contains `vector(384)`, a document foreign key, uniqueness constraints, and an HNSW cosine index.
- [x] Re-running sync and ingestion is idempotent and changed document content replaces stale chunks.
- [x] The existing Databricks App has been redeployed from source path `homework-2` and is running.
- [x] Chicago and Austin documents exist in Lakebase (28 documents total; sync run `1124595407067729`).
- [x] The embedding job populated 28 rows in `weather_hw2.weather_embeddings` (run `1057545523950082`).
- [x] The same repository path used by `POST /weather/search` returned five ranked live results
      for “flooding or severe weather risk” (run `925919958451100`).
- [x] Live schema verification confirmed `vector(384)`, the HNSW cosine index, and the document
      foreign key (run `1068987780563373`).
- [x] Evidence images contain no credentials, tokens, or secret values.

## Reflection

The key technical correction from the lab was removing Spark JDBC from the Lakebase write path.
The homework writes document and embedding batches directly with `psycopg2`, including the
pgvector cast in the insert statement, so there is no fragile array staging or manual post-write
conversion. The deployment exposed a second environment-specific correction: Databricks
serverless Python tasks already provide a native `psycopg2`, and adding `psycopg2-binary` to the
task overlay aborted the kernel with `SIGABRT`. Removing that overlay dependency made ingestion
succeed; the separate Databricks App build still installs its own wheel. The next improvement
would be a durable geocoding cache and a scheduled alert refresh; both are deliberately outside
the required retrieval pipeline.
