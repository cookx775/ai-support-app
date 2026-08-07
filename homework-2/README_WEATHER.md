# Weather Intelligence

A Flask REST API that harvests narrative weather data, stores it in Lakebase, embeds it with
`sentence-transformers/all-MiniLM-L6-v2`, and retrieves semantically similar passages through
Postgres `pgvector`.

## Data source

Weather text comes from the public [National Weather Service API](https://www.weather.gov/documentation/services-web-api).
It requires no API key and supplies two useful forms of unstructured text:

- active alert descriptions and safety instructions;
- multi-period `detailedForecast` narratives.

City names are resolved to coordinates with OpenStreetMap Nominatim. The client identifies
itself, restricts results to the US, caches results for the life of the app process, and limits
geocoding to one request per second as required by the
[Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/). Explicit
coordinates bypass geocoding. OpenStreetMap data is © OpenStreetMap contributors, ODbL 1.0.

## Architecture and schema

```text
POST /weather/sync
    -> Nominatim (city inputs only)
    -> NWS points + forecast + active-alert endpoints
    -> weather_hw2.weather_documents

jobs/ingest_weather_embeddings.py
    -> 800-character chunks with 100-character overlap
    -> all-MiniLM-L6-v2 normalized 384-dimension vectors
    -> weather_hw2.weather_embeddings vector(384) + HNSW index

POST /weather/search
    -> same MiniLM model
    -> cosine distance with pgvector <=>
    -> ranked JSON matches
```

`weather_documents` keeps normalized fields, a SHA-256 content hash, and a provenance envelope
containing the raw NWS item and source URL. `weather_embeddings` has a cascading foreign key to
the document, one row per chunk, and uniqueness on document/chunk/model. When source text
changes, the ingestion job replaces every chunk for that document in one transaction.

The DDL is versioned in `sql/schema.sql` and is executed by both the app and ingestion job. All
Lakebase writes use `psycopg2`; embeddings are passed directly to `%s::vector`. Spark/JDBC and
post-write array casts are intentionally not used.

## Configuration

The app and ingestion job use the same native Lakebase role. Connection resolution is:

1. `LAKEBASE_URL`, when set for local development; otherwise
2. the Databricks secret named by `LAKEBASE_SECRET_SCOPE` and `LAKEBASE_SECRET_KEY`, which
   default to `database/lakebase-url`.

The secret must contain a standard SSL-enabled PostgreSQL URL. Never write it to source, logs,
screenshots, or submission archives. The Databricks App service principal and the identity that
runs the embedding job both need permission to read the secret.

## Run locally

Python 3.9 or later is supported.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export LAKEBASE_URL='postgresql://...?...sslmode=require'
pytest -q
python app.py
```

The sentence-transformers model is loaded lazily on the first search. The first request can
therefore be slower while the model downloads and Lakebase resumes from scale-to-zero.

## Run the pipeline

1. Start the Flask app. It creates the `weather_hw2` schema and tables from `sql/schema.sql`.
2. Sync weather documents:

   ```bash
   curl -X POST http://localhost:8000/weather/sync \
     -H 'Content-Type: application/json' \
     -d '{"locations":["Chicago, IL",{"lat":30.2672,"lon":-97.7431,"label":"Austin, TX"}],"limit":50}'
   ```

   For deployment verification when the App URL is protected by Databricks user authorization,
   `jobs/sync_weather_documents.py` provides the same client/repository path as a one-time
   Git-sourced Python task. It defaults to Chicago and Austin and accepts repeated `--location`
   arguments.

3. Embed all documents whose current content hash has not been processed:

   ```bash
   python jobs/ingest_weather_embeddings.py
   ```

   Optional flags are `--limit`, `--chunk-size`, and `--chunk-overlap`. In Databricks, run the
   file as a Git-sourced Python script task at
   `homework-2/jobs/ingest_weather_embeddings.py`; it reads `database/lakebase-url` through the
   Databricks SDK. Configure the task's environment/libraries with these PyPI dependencies before
   its first run; Python script tasks do not inherit the Databricks App build environment:

   ```text
   databricks-sdk>=0.30.0,<1
   sentence-transformers>=3.0.0,<6
   ```

   Do **not** add `psycopg2` or `psycopg2-binary` to the serverless job environment. Databricks
   Runtime already supplies the native driver; overlaying another wheel can abort the Python
   kernel with `SIGABRT` during import. The App build is a separate environment and still uses
   `psycopg2-binary` from `requirements.txt`.

4. Search:

   ```bash
   curl -X POST http://localhost:8000/weather/search \
     -H 'Content-Type: application/json' \
     -d '{"query":"flash flood risk this weekend","top_k":5}'
   ```

   `jobs/search_weather.py` is the corresponding one-time Git-sourced verification task for an
   App deployment whose user-authorization proxy prevents unattended REST calls. It uses the
   same query model and repository cosine-search method as `POST /weather/search`.

5. Verify the live Lakebase objects with `jobs/verify_lakebase_schema.py`. The read-only task
   reports document and embedding counts, the `vector(384)` column type, the document foreign
   key, and the HNSW cosine index without exposing connection details.

Supported sync locations are city strings, `{lat, lon, label}` objects, and two-number
`[lat, lon]` pairs. `limit` is clamped to 1–50 per location; `top_k` is clamped to 1–20.

## Deploy in the existing Databricks App slot

1. Push this repository to `main`.
2. Open the existing `ai-support-app` Databricks App and deploy using a different source.
3. Keep the same public Git repository and branch, but set **Source code path** to `homework-2`.
4. Confirm the app service principal can read the `database/lakebase-url` secret.
5. Deploy, inspect startup logs, then open `/healthz`.
6. Run the sync request, execute the embedding script as a Git-sourced Python task, and run the
   search request.

Redeploying replaces the Day 1 UI but does not delete its source snapshot or Lakebase tables.
The existing app resource is reused so a separate slot remains available for the capstone.

## Verification SQL

```sql
SELECT source_type, location, COUNT(*)
FROM weather_hw2.weather_documents
GROUP BY source_type, location
ORDER BY location, source_type;

SELECT COUNT(*) AS chunks, vector_dims(embedding) AS dimensions, model_name
FROM weather_hw2.weather_embeddings
GROUP BY vector_dims(embedding), model_name;

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'weather_hw2.weather_embeddings'::regclass;

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'weather_hw2';
```

## Known limitations

- NWS provides active alerts, not an alert archive, so results vary with current conditions.
- Nominatim's public service is appropriate only for this low-volume homework. A production app
  should use a durable geocoding cache or managed geocoder.
- The model cache is local to each compute environment; the app and job download separate copies.
- The service performs retrieval only. It does not generate an LLM summary or schedule refreshes.
