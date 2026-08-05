# Databricks Free Edition — AI, Vector Search, and Agent Capabilities

Last verified: **2026-08-05**

This note records the platform capabilities the capstone depends on: the embedding and
retrieval path, whether an agent can take real write actions, and whether Spark is usable
for ingest. It answers open questions 1–3 of `../capstone-brief.md`.

Scope note: these facts are corpus-agnostic and survive a change of capstone candidate.
Candidate-specific data-source findings live in `capstone-candidate-feasibility.md`.

## Verified Free Edition limits

- Free Edition provides **serverless compute only**; custom compute configurations are not
  supported. [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- Per-account caps: **3 Databricks Apps** (each auto-stops 24 hours after start, update, or
  redeploy), **1 Lakebase project** with scale-to-zero, **1 SQL warehouse** (2X-Small
  maximum), **1 AI Search endpoint** (1 search unit), and **1 Lakeflow pipeline per pipeline
  type**. [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- **Maximum 5 concurrent job tasks per account.** Exceeding quota shuts down compute for the
  remainder of the day, and in extreme cases the month; data and settings are retained.
  [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- Unsupported: R and Scala, **custom workspace storage locations**, online tables, clean
  rooms, SSO/SCIM, and account console/API access. One workspace and one metastore per
  account. [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- Free Edition is for non-commercial use with no guaranteed reliability, support, or SLA.
  [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)

The **1 SQL warehouse** and **1 AI Search endpoint** caps were not previously recorded and
matter for planning: the AI Search endpoint is a single, non-reusable resource.

## Q1 — vector search and embedding paths

Two independent paths exist. The brief's open question 1 asked whether Mosaic Vector Search
is available on Free Edition, or whether embeddings must come from a foundation-model
endpoint with vectors stored in Lakebase. **The answer is that both work.** The concern that
Free Edition might have no vector search path was unfounded — the product was renamed, not
withdrawn.

### Path A — Databricks AI Search (the renamed product)

- Mosaic AI Vector Search was **renamed**: "Databricks AI Search (formerly Databricks Vector
  Search)". Searching for the old name is why it can appear to be missing.
  [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- Requirements: a Unity Catalog enabled workspace, serverless compute, a source Delta table
  with **Change Data Feed enabled**, and `CREATE TABLE` privilege on the target schema.
  [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- Free Edition grants 1 endpoint / 1 search unit and states **Direct Vector Access is
  unsupported**. Only the **Delta Sync** index type is therefore usable.
  [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations),
  [Create a vector search index](https://docs.databricks.com/gcp/en/vector-search/create-vector-search)
- The index-creation docs state the storage prerequisite in full as: "For standard
  endpoints, the source table must have Change Data Feed enabled." There is no
  storage-location or catalog-type clause.
  [Create a vector search index](https://docs.databricks.com/aws/en/vector-search/create-vector-search)
- Triggered and Continuous sync modes differ only in *when* the sync runs; both require CDF.
  [Create a vector search index](https://docs.databricks.com/aws/en/vector-search/create-vector-search)
- Retrieval from SQL uses the **`vector_search()`** function, which requires serverless
  compute and is unavailable on Pro/Classic SQL warehouses.
  [vector_search function](https://docs.databricks.com/aws/en/sql/language-manual/functions/vector_search)

### Path B — Lakebase Postgres with pgvector

- Lakebase supports pgvector natively. The extension registers under the name **`vector`**
  (not "pgvector"), version 0.8.0 on both PG16 and PG17, providing the vector data type plus
  **`ivfflat` and `hnsw`** access methods. The command is `CREATE EXTENSION vector;`.
  [Lakebase extensions](https://docs.databricks.com/aws/en/oltp/projects/extensions)
- No preview gating, no admin opt-in, and no consumption of the single AI Search endpoint.

### Embedding generation

- `ai_query()` requires serverless compute, is unavailable on Pro/Classic SQL warehouses,
  and needs a model-serving endpoint.
  [ai_query function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- There is **no standalone embedding SQL function**. The AI Functions family covers
  `ai_parse_document`, `ai_extract`, `ai_classify`, `ai_summarize`, `ai_similarity`, and
  `ai_gen`, but embeddings come via `ai_query()` against an embedding endpoint, or
  implicitly through a Delta Sync index using Databricks-managed embeddings.
  [AI Functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- `ai_prep_search` (Beta) converts `ai_parse_document` output into RAG-ready chunks
  (`chunk_id`, `chunk_to_embed`, `chunk_to_retrieve`, `pages`).
  [ai_prep_search function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_prep_search)
- `databricks-gte-large-en` (1024-dimension, 8K token window) and `databricks-bge-large-en`
  are Databricks-hosted pay-per-token embedding endpoints.
  [Supported foundation models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)

**Not confirmed:** no documentation states a Free-Edition-specific quota or cost for
Foundation Model API pay-per-token usage. The general "exceed quota, lose compute for the
day" rule presumably applies. Treat as an empirical risk.

## Change Data Feed is available on Free Edition

**Scope of this section.** `../capstone-brief.md` states that CDF → Delta is not a capstone
requirement, and adds that it cannot be demonstrated on Free Edition. The
*requirement* question is settled by the bootcamp instructor's communication and the
published spec, and nothing here touches it — CDF remains optional and not worth
engineering around. What follows addresses only the separate **technical** claim about
Free Edition, because the retrieval architecture depends on it: Databricks AI Search
requires CDF, so if CDF were unavailable, one of the two vector paths would be closed.

On that technical question, the documentation does not support the restriction:

- CDF's documented requirements are a supported table format registered in Unity Catalog
  with **row tracking** enabled (or Iceberg v3), plus a runtime bar. Legacy CDF uses the
  `delta.enableChangeDataFeed = true` table property. **No requirement mentions storage
  location, storage credentials, or external locations.**
  [Change data feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- Row tracking has been available since DBR 14.1, well below what serverless runs.
  [Row tracking](https://docs.databricks.com/aws/en/delta/row-tracking)

The genuine restriction is narrower and unrelated: Free Edition does not permit configuring
**your own** cloud bucket as a managed-storage root, which is what "custom workspace storage
locations are unsupported" means. Free Edition catalogs already have Databricks-provisioned
managed storage, and CDF has no dependency on whose account holds the bytes.

**Local observation, not a documentation claim:** the original error was not reproduced in
this pass. A plausible explanation is an entitlement message on a *trial* workspace, which
is a different product from Free Edition. Anyone re-encountering a CDF failure should
capture the literal error text rather than infer the cause.

## Q2 — agent write-action paths

Component 5 of the capstone requires tools that take **real write actions**, and open
question 2 asked whether an Agent Bricks agent on Free Edition can be given custom write
tools. Three options were examined; the recommended one avoids the question entirely.

- **Databricks Apps service principal (recommended).** Each app is issued a dedicated
  service principal with `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` injected
  automatically; you grant that principal permissions on target resources directly. A tool
  is then an ordinary Python function running a parameterized `INSERT` through the app's
  existing database connection. Fully documented, no preview gating, no sandboxing.
  [Databricks Apps authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- **Unity Catalog functions as agent tools.** Execution is sandboxed with temporary disk and
  limited network access. The documentation carries a governance warning — "Executing
  arbitrary code in an agent tool can expose sensitive or private information" — and
  describes service policies as the mechanism for restricting which tools may act.
  [Create a custom agent tool](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)
  **No explicit statement either permits or forbids writes from a UC function.** Treating
  writes as allowed is an inference from absence of a restriction, not a documented capability.
- **Agent Bricks.** Databricks announced its addition to Free Edition alongside Lakebase,
  Serverless GPUs, and Lakeflow Designer.
  [What's coming next for Free Edition](https://www.databricks.com/blog/whats-coming-next-free-edition)
  Regional rollout timing is not documented; community reports of US-region-first
  availability are **unconfirmed**. Verify in the actual workspace before depending on it.

## Q3 — Spark behaviour on serverless

Open question 3 asked whether Spark is usable meaningfully for ingest, or whether the
pipeline collapses into notebook Python. **It is real Spark**, with specific exclusions.

- The Spark DataFrame API, `spark.sql`, and Delta/UC reads and writes are available.
  **Only Spark Connect APIs are supported; the RDD API is not.**
  [Serverless compute limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- Also unsupported: Scala and R in notebooks, JAR libraries, compute-scoped libraries, and
  the DataFrame caching APIs `.cache()`, `.persist()`, and `.checkpoint()`. External data
  sources must go through Unity Catalog. Maximum serverless job runtime is 7 days;
  `spark.createDataFrame` from local data has a 128 MB row-size cap.
  [Serverless compute limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- Jobs run on serverless job compute and schedule normally, subject to the 5-concurrent-task
  account cap. [Run jobs on serverless compute](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)

This is sufficient for a genuine Spark pipeline; the ingest does not collapse into notebook
Python.

## Verified Databricks Apps behaviour

- Supported frameworks include Streamlit, Dash, and Gradio for Python, and React, Angular,
  Svelte, and Express for Node, plus "most Python-based application frameworks".
  [Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- Default app size is up to 2 vCPU / 6 GB RAM, with a Large tier up to 4 vCPU / 12 GB.
  [App compute size](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/compute-size)
- Default **app authorization** runs everything as the app service principal, so all users
  share its permissions. **On-behalf-of-user** authorization forwards the signed-in user's
  token against declared OAuth scopes when per-user enforcement is needed.
  [Databricks Apps authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- Automatic deployment on push requires a **private** repository plus a Git credential for
  the app service principal; public repositories deploy manually without a credential.
  [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)

## Verified Lakebase connection behaviour

- Connections use the standard Postgres wire protocol, with OAuth credentials generated via
  `generate_database_credential()` and supplied as the password for the role matching the
  service principal's client ID.
  [Lakebase authentication](https://docs.databricks.com/aws/en/oltp/instances/authentication)
- Both the workspace OAuth token and the derived database credential **expire after 60
  minutes**. Expiry is enforced at connection time only; already-open connections survive.
  Refresh at roughly 50 minutes.
  [Connect external apps to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect)
- The built-in PgBouncer pooler **does not support OAuth authentication**. Pooling therefore
  requires either native password roles or handling token refresh at the pool layer.
  [Connect external apps to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect)

The Day 1 application already implements the refresh-per-connection pattern in
`support_app/db.py`, which remains the working reference.

## Lakebase Search — what enabling it does

"Lakebase search" is a distinct, Beta, project-level feature — not the same thing as
pgvector, and not the same thing as Databricks AI Search.

- It provisions two extensions: **`lakebase_vector`**, adding a `lakebase_ann` index type
  described as a drop-in companion to pgvector (`CREATE EXTENSION IF NOT EXISTS
  lakebase_vector CASCADE;` installs plain `vector` as a dependency), and **`lakebase_text`**,
  adding BM25 full-text search via a `lakebase_bm25` index type.
  [Lakebase Search](https://docs.databricks.com/aws/en/oltp/projects/lakebase-search),
  [Lakebase vector](https://docs.databricks.com/aws/en/oltp/projects/lakebase-vector)
- Enabling it requires admin opt-in from the workspace Previews page, **restarts all computes
  in the project, and is irreversible**.
  [Lakebase Search](https://docs.databricks.com/aws/en/oltp/projects/lakebase-search)

**Not confirmed:** the documentation does not state whether Lakebase Search is available on
Free Edition specifically. It is gated behind an admin Previews toggle, and Free Edition has
no account console — treat availability as unverified. Plain `pgvector` is unaffected either
way.

## Project decisions

These are implementation choices for the capstone, not platform requirements.

- **Use Lakebase `pgvector` as the primary retrieval path.** It requires no new
  infrastructure: the OAuth psycopg pool in `support_app/db.py` already works, so the
  addition is one `CREATE EXTENSION vector;`, one vector column, an hnsw index, and writes
  through a connection already proven in production.
- **Treat Databricks AI Search as a stretch goal**, layered on only after an end-to-end demo
  exists. It is capable and documented, but it consumes the single AI Search endpoint and
  introduces CDF configuration, a sync job, embedding configuration, and a query surface
  separate from the app's database connection — two stores to keep consistent, under a
  three-day deadline.
- A secondary reason favours pgvector for this specific capstone: retrieval, agent state,
  and the write tool's target all live in the same Postgres, so there is no cross-store
  consistency question to answer during a demo.
- **Implement the agent loop in Python inside the Databricks App**, with tools as ordinary
  functions writing through the app service principal's Lakebase credential. This avoids
  both the undocumented status of UC-function writes and the unverified regional
  availability of Agent Bricks.
- **Do not enable Lakebase Search** unless a specific need appears. It is Beta, irreversible,
  and restarts project computes, and pgvector covers the same core requirement.

## First-party references

- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [Create a vector search index](https://docs.databricks.com/aws/en/vector-search/create-vector-search)
- [vector_search function](https://docs.databricks.com/aws/en/sql/language-manual/functions/vector_search)
- [ai_query function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [ai_prep_search function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_prep_search)
- [AI Functions on Databricks](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [Foundation model API supported models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [Change data feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [Row tracking](https://docs.databricks.com/aws/en/delta/row-tracking)
- [Lakebase extensions](https://docs.databricks.com/aws/en/oltp/projects/extensions)
- [Lakebase Search](https://docs.databricks.com/aws/en/oltp/projects/lakebase-search)
- [Lakebase vector](https://docs.databricks.com/aws/en/oltp/projects/lakebase-vector)
- [Lakebase authentication](https://docs.databricks.com/aws/en/oltp/instances/authentication)
- [Connect external apps to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect)
- [Create a custom agent tool](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)
- [Serverless compute limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- [Run jobs on serverless compute](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)
- [Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [App compute size](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/compute-size)
- [Databricks Apps authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- [What's coming next for Free Edition](https://www.databricks.com/blog/whats-coming-next-free-edition)
