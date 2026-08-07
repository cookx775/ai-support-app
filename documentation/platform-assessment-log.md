# Platform Assessment Log

Running evidence for the written pros/cons assessment (deliverable D5 in
`delivery-plan.md`). **Append as things happen, not afterward.**

## Why this file is contemporaneous

The assessment's credibility comes entirely from specifics — the exact limit, the exact
undocumented behaviour, how long the workaround took. Those details are free to record at the
moment they occur and effectively unrecoverable a week later, when what remains is a vague
impression that something was annoying. An assessment built on vague impressions is not
evidence, and it is the deliverable that leadership actually reads.

## What to record

One entry per friction point or capability confirmation. Keep it factual; the argument gets
written later, from these.

- **What happened** — the observable behaviour, not the interpretation.
- **Cost** — time lost, or the workaround required.
- **Whether documentation covered it** — this distinction is the most useful signal in the whole
  file. A hard platform that documents itself honestly is a different proposition from an easy
  one that does not.
- **Whether it is a Free Edition limit or a platform property.** Do not let Free Edition's
  quotas contaminate the judgement of the platform an employer would actually buy.

Capability wins belong here too. A log of only complaints is not an assessment.

## Sensitivity

This repository is public. Record the platform behaviour, never the employer, its stack, its
people, or the evaluation's stakes. See the sensitivity rule in `README.md`.

---

## Entries

### 2026-08-05 — Lakebase OAuth credential rotation (retrospective, Day 1)

Recorded after the fact, which is exactly the habit this file exists to replace.

- **What happened:** connecting a Databricks App to Lakebase requires requesting a fresh OAuth
  database credential per connection, because the credential expires after one hour. The request
  needs the endpoint's **resource name** (`projects/<p>/branches/<b>/endpoints/<e>`), not the
  UUID-style identifier the Lakebase UI displays more prominently.
- **Cost:** the single hardest part of Day 1.
- **Documentation:** covered by the first-party autoscaling tutorial, but the UI actively steers
  toward the wrong identifier. Documented correctly, discoverable poorly.
- **Classification:** platform property, not a Free Edition limit.
- **Verdict:** genuinely good design — no database password exists to leak — with a real
  onboarding cost that a first-party quickstart should absorb rather than hand to the developer.

### 2026-08-05 — Documentation is silent on multiple apps sharing one Lakebase database

- **What happened:** attaching a Lakebase resource to an app creates a Postgres role named for
  the app's service principal and grants it `CONNECT`/`CREATE` on the database. Nothing in the
  first-party documentation addresses what happens with a **second** app on the same database:
  no guidance on schema isolation, cross-role grants, or which identity should own DDL. Local
  development and Spark jobs each add further identities again.
- **Cost:** found by reasoning ahead rather than by failing, so the cost was avoided rather than
  paid. The latent failure is severe and badly signposted — the app deploys and starts cleanly,
  then fails at query time with `permission denied for table`.
- **Documentation:** **not covered.** The single-app path is documented well; the multi-app path
  is undocumented, and it is not an exotic scenario.
- **Classification:** platform property. Free Edition's one-project limit *forces* the shared
  database and so makes the gap unavoidable here, but the same ambiguity exists on paid tiers.
- **Verdict:** the automatic role creation is good ergonomics for the first app and an unmapped
  edge for the second. An evaluation should assume identity and grant management is work the
  team owns, and that documentation will not lead it.

### 2026-08-05 — Small defaults that cost real time

Individually trivial, cumulatively the texture of the developer experience. Recorded because an
assessment built only on architecture misses where the hours actually go.

- `databricks apps run-local` defaults `--entry-point` to **`app.yml`**, while every Databricks
  App example and the deployed runtime use **`app.yaml`**. The local command therefore does not
  find the file that the platform itself generates.
- The Lakebase UI displays a UUID more prominently than the `projects/.../endpoints/...`
  resource name that the credential API requires (the Day 1 entry above).
- No single app file may exceed **10 MB**, and the failure surfaces at deploy time rather than
  at commit time.
- **Classification:** platform properties, all documented somewhere and none discoverable at the
  moment of use. The pattern is consistent enough to be worth naming in the assessment: the
  documentation is accurate, and the product does not surface it where the decision is made.

### 2026-08-06 — Lakebase vector writes through Spark JDBC were not a stable path

- **What happened:** the Day 2 lab route reached the vectorization stage but failed near the end
  of the workbook. The instructor repository then cycled through raw JDBC and Spark JDBC fixes
  before returning to driver-side `psycopg2`. Spark JDBC could not reliably express the required
  Postgres upsert and pgvector write semantics in this environment.
- **Cost:** the original workbook path consumed the lab session without producing a complete
  retrieval pipeline. Homework 2 was rebuilt around direct batched PostgreSQL writes and
  `%s::vector` casts rather than trying to rescue that path.
- **Documentation:** the corrected guidance arrived as repository commits after the class. The
  assignment itself now explicitly prohibits `spark.write.jdbc` for Lakebase writes.
- **Classification:** integration/tooling limitation, not a Free Edition quota.
- **Verdict:** Lakebase's native PostgreSQL surface is a strong escape hatch, but the advertised
  Spark-to-operational-database transition was materially less seamless than the platform model
  suggests. Use Spark for transformation and a native database driver for operational writes.

### 2026-08-06 — Federated workspace login failed in the embedded browser again

- **What happened:** opening the app-management page reached Databricks sign-in, but the
  federated OIDC callback ended on a browser-level "site can't be reached" failure. The same
  failure occurred during Homework 1; it is upstream of application deployment and logs.
- **Recovery:** opening a fresh workspace tab with the signed-in session restored access, and the
  app deployment plus job runs could continue. The protected `databricksapps.com` app domain
  remained blocked in the controlled browser, while the workspace deployment status and job
  output remained accessible.
- **Cost:** the failed callback interrupted the workflow and required a fresh authenticated tab;
  it did not indicate an application-code failure.
- **Documentation:** no useful recovery guidance was surfaced at the failure point.
- **Classification:** authentication/browser integration friction, not a Free Edition quota and
  not an application-code failure.

### 2026-08-06 — Overlaying psycopg2 crashed a serverless Python task

- **What happened:** the Homework 2 job initially installed `psycopg2-binary` into a serverless
  environment. Importing it from the ephemeral environment aborted the Python kernel with
  `SIGABRT`. The instructor's corrected Day 2 material explicitly uninstalls both psycopg2
  distributions before restarting Python because Databricks Runtime already supplies a native
  driver.
- **Recovery:** remove both psycopg2 distributions from the job dependency overlay and use the
  runtime-provided driver. The same ingestion then completed and inserted 28 embedding chunks.
  The Databricks App build remains a separate environment and correctly installs
  `psycopg2-binary` itself.
- **Cost:** one failed job run plus the time needed to distinguish an ABI/runtime conflict from a
  database or application defect.
- **Classification:** serverless runtime/library compatibility, not a Lakebase limitation.
- **Verdict:** dependency guidance needs to distinguish App builds from serverless task
  environments. Reusing an ordinary Python requirements file across them is unsafe when native
  packages overlap with the managed runtime.
