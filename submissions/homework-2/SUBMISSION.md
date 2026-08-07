# Day 2 Homework Submission

## Deliverables

- **Databricks App URL:** https://ai-support-app-7474657586545240.aws.databricksapps.com
- **Complete upload archive:** `weather-intelligence-submission.zip`
- **Deployed service screenshot:** pending live deployment
- **Semantic search screenshot:** pending live deployment
- **Lakebase tables/vector screenshot:** pending live deployment

## Verification checklist

- [x] Local tests cover harvesting, normalization, chunking, vector insertion, retrieval, and API validation.
- [x] Embeddings are written by `psycopg2` with a direct `%s::vector` cast.
- [x] The schema contains `vector(384)`, a document foreign key, uniqueness constraints, and an HNSW cosine index.
- [x] Re-running sync and ingestion is idempotent and changed document content replaces stale chunks.
- [ ] The existing Databricks App has been redeployed from source path `homework-2`.
- [ ] Chicago and Austin documents exist in Lakebase.
- [ ] The embedding job has populated `weather_hw2.weather_embeddings`.
- [ ] `POST /weather/search` returns ranked live results.
- [ ] Screenshots contain no credentials, tokens, or secret values.

## Reflection

The key technical correction from the lab was removing Spark JDBC from the Lakebase write path.
The homework writes document and embedding batches directly with `psycopg2`, including the
pgvector cast in the insert statement, so there is no fragile array staging or manual post-write
conversion. The next improvement would be a durable geocoding cache and a scheduled alert
refresh; both are deliberately outside the required retrieval pipeline.
