# Day 2 Homework Submission

## Graded result

**100/100** on 2026-08-07: Harvest 25/25, Vectorize 30/30, Retrieve 30/30, and
Documentation 15/15. The detailed grading record is preserved in `GRADING.md`. This submission
is now closed and should change only to correct a factual error.

## Deliverables

- **Databricks App URL:** https://ai-support-app-7474657586545240.aws.databricksapps.com
- **Complete upload archive:** `weather-intelligence-submission.zip`
- **Deployed service evidence:** `screenshots/deployed-app.png`
- **Semantic search evidence:** `screenshots/semantic-search.png`
- **Lakebase tables/vector evidence:** `screenshots/lakebase-vectors.png`
- **Native Databricks deployment view:** `screenshots/native-databricks-deployment.jpg`
- **Native Databricks semantic-search run:** `screenshots/native-databricks-search-job.jpg`
- **Native Databricks Lakebase verification run:** `screenshots/native-databricks-lakebase-job.jpg`
- **Direct Lakebase document rows:** `screenshots/native-lakebase-tables.jpg`
- **Direct Lakebase vector rows:** `screenshots/native-lakebase-embeddings.jpg`

The summary cards transcribe credential-free fields from the live Databricks deployment and
job-run pages. The native workspace captures are included alongside them for authenticity, and
exact run IDs allow the results to be reopened in Databricks.

## Verification checklist

- [x] Local tests cover harvesting, normalization, chunking, vector insertion, retrieval, and API validation.
- [x] Embeddings are written by `psycopg2` with a direct `%s::vector` cast.
- [x] The schema contains `vector(384)`, a document foreign key, uniqueness constraints, and an HNSW cosine index.
- [x] Re-running sync and ingestion is idempotent and changed document content replaces stale chunks.
- [x] The existing Databricks App has been redeployed from source path `homework-2` and is running.
- [x] Chicago and Austin documents exist in Lakebase (28 documents total; sync run `1124595407067729`).
- [x] The embedding job populated 28 rows in `weather_hw2.weather_embeddings` (run `1057545523950082`).
- [x] The same model and repository search path used by `POST /weather/search` returned five
      ranked live results for “flooding or severe weather risk” (run `925919958451100`).
- [x] Live schema verification confirmed `vector(384)`, the HNSW cosine index, and the document
      foreign key (run `1068987780563373`).
- [x] Direct Lakebase Tables views show both Homework 2 tables, 28 rows, the
      `embedding vector(384)` column, the MiniLM model, and document relationship links.
- [x] Evidence images contain no credentials, tokens, or secret values.

## Remaining deployment-proof limitation

The deployed endpoint is protected by Databricks interactive user authorization. A serverless
job request using its SDK identity was redirected to the workspace OAuth consent flow rather
than forwarded to Flask, so the job result is not presented as REST proof. The native search-run
capture proves live Lakebase retrieval through the same model/repository code, while a literal
curl/Postman screenshot of `POST /weather/search` remains a recommended authenticated manual
capture before submission if the rubric requires gateway-level evidence.

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
