# Capstone App Runbook

Last verified: **2026-08-05** · Status: **doc-verified, not yet executed**

Front-loaded mechanics for the capstone app, produced by a wayfinder pass over first-party
documentation before any build session. The point is that build sessions on Aug 6–9 spend their
time on the product, not on rediscovering how Databricks Apps, Lakebase roles, and Git-sourced
jobs fit together.

**Read the "Verification status" markers.** Everything here is drawn from first-party docs, but
docs and UI diverge — Day 1 proved that when the Lakebase UI displayed a UUID where the API
needed a resource name. Items marked ⚠️ **UNVERIFIED** are doc-derived and untested on this
account; confirm them at the first opportunity and correct this file in place.

---

## Locked decisions

| Decision | Choice | Why |
|---|---|---|
| Repository | **Separate public repo**, app at its root | Chosen 2026-08-05 after establishing that a subdirectory would also work. Source path at root is the simplest deploy config |
| App source path | Repository root (leave the field empty) | |
| Vector store | `pgvector` — extension `vector` **0.8.0**, `CREATE EXTENSION vector` | Supported with **no preview gating**. Avoid `lakebase_vector`: it requires enabling Lakebase Search, which is irreversible and restarts all project computes, and uses IVF/RaBitQ rather than HNSW |
| Embedding dimension | **`vector(1024)`** | Every candidate endpoint is 1024-dim, so the schema does not depend on which one Free Edition exposes |
| Embedding endpoint | `databricks-gte-large-en` (8192-token window); fallback `databricks-bge-large-en` (512-token) | Prefer GTE — Federal Register notices are long, and a 512-token window forces smaller chunks |
| Agent | Hand-rolled Python tools inside the app | Already decided in `capstone-brief.md`; the documented path |
| Spark jobs | **Git provider source** on a remote repo, no Git folder | Task paths are repo-relative |
| **DDL ownership** | **The app owns all DDL. Jobs write data only.** | See "The identity trap" below — this is the most important rule in this file |

## Repository layout

The app's source path is the repo root, so `app.py`, `app.yaml`, and `requirements.txt` must sit
there. Job code lives in the same repo but is referenced by *relative path* from the job task,
which is independent of the app's source path.

```text
Tariff-Copilot/                 <- separate public repo, its own remote
├── app.py                      <- Streamlit entry point (app source = root)
├── app.yaml                    <- command + env, incl. ENDPOINT_NAME
├── requirements.txt
├── requirements-dev.txt
├── tariff_app/                 <- domain, models, repository, db, agent
│   ├── db.py                   <- COPY from support_app/db.py, do not rewrite
│   ├── domain.py
│   ├── models.py
│   ├── repository.py
│   └── agent.py
├── jobs/                       <- Git-sourced job tasks (relative paths)
│   ├── ingest_hts.py
│   └── ingest_federal_register.py
├── sql/
│   ├── schema.sql              <- DDL; required in the submission ZIP
│   └── grants.sql
└── tests/
```

**Hard limit: no single app file may exceed 10 MB** or deployment fails. The 35,789-record HTS
snapshot therefore must **not** live in the repo's app source path — it belongs in a Delta table
or a volume, written by the ingest job.

## One-time setup

1. Create the public GitHub repo under `cookx775`.
2. Clone it as a **sibling directory on this drive**, beside `Databricks Bootcamp/`.
3. Set the commit identity locally so it matches the workspace repo:
   ```bash
   git config user.name  "Dalton Cook"
   git config user.email "cookx775@users.noreply.github.com"
   ```
4. Authorization is separate from identity, and it is per-machine. If this machine has never
   pushed, see the `gh auth` sequence in `README.md` — `gh auth setup-git` is not optional with
   the `osxkeychain` helper.
5. Verify with `git push --dry-run` **before** writing code, not after.

Two remotes now exist. The exFAT corruption risk applies to both: push each after every
meaningful chunk.

## The local development loop

This is the largest time saver available and it should be established before any feature work.
A deploy cycle per change will not fit in the remaining hours.

```bash
databricks apps run-local --entry-point app.yaml --prepare-environment
```

| Flag | Default | Note |
|---|---|---|
| `--entry-point` | `app.yml` | ⚠️ **Our file is `app.yaml`. Pass this explicitly or it will not be found.** |
| `--app-port` | 8000 | The app itself |
| `--port` | 8001 | The app *proxy* — a second port is in play |
| `--prepare-environment` | false | Sets up the environment; **requires `uv` installed** |
| `--env` | — | Set environment variables |
| `--debug` / `--debug-port` | — | Debug mode and debugger port |

Local runs need Databricks CLI authentication. The `PG*` variables are injected only in the
deployed runtime, so locally they must be supplied by hand from the Lakebase UI plus a token
minted through `WorkspaceClient` — the same pattern HW1's README already documents.

⚠️ **The local loop authenticates as your user, not as the app's service principal.** That
difference is not cosmetic; see the next section.

## Lakebase wiring, and the identity trap

Adding a Lakebase resource to an app (permission level **"Can connect and create"** — currently
the only one) causes Databricks to create a Postgres role **named after the app's service
principal client ID** and grant it `CONNECT` and `CREATE` on the selected database. It injects
six variables: `PGAPPNAME`, `PGDATABASE`, `PGHOST`, `PGPORT`, `PGSSLMODE`, `PGUSER`.

There is no `PGPASSWORD`. The password is an OAuth database credential that **expires after one
hour**, which is why the pool mints a fresh one per connection, and why `ENDPOINT_NAME` must be
the `projects/<p>/branches/<b>/endpoints/<e>` **resource name** rather than the UUID the UI
shows more prominently. Copy `support_app/db.py` rather than reimplementing this.

### The trap

The capstone introduces a **second** app, therefore a **second** service principal, therefore a
**second** Postgres role — and the Spark jobs and your local dev sessions run as *further*
identities again. Postgres grants privileges to the creating role, so:

> Tables created by your user during local development, or by a Spark job running as you, are
> owned by **your** role. The deployed app's service principal role has no privileges on them.

The symptom is nasty because it is late and misleading: the app builds, deploys, and starts
cleanly, then fails at query time with `permission denied for table …`. Nothing in the deploy
output hints at it. The Lakebase resource documentation is **silent** on multi-app sharing and
schema isolation, so there is no first-party guidance to fall back on.

### The rule that avoids it

**The app owns all DDL; jobs write data only.** The app creates its schema and tables during
startup — exactly the pattern `support_app/repository.py` already uses and which is already
proven on this account. Everything the app later reads is then owned by the app's own role.

Where a job must create a table, grant explicitly, and include default privileges so *future*
tables are covered too:

```sql
-- <app_sp> is the capstone app's service principal client ID (its PGUSER value).
GRANT USAGE ON SCHEMA tariff TO "<app_sp>";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tariff TO "<app_sp>";

-- Covers tables created later. Default privileges attach to the CREATING role,
-- so name it explicitly rather than relying on the current session's role.
ALTER DEFAULT PRIVILEGES FOR ROLE "<creating_role>" IN SCHEMA tariff
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "<app_sp>";
```

⚠️ **UNVERIFIED.** The `ALTER DEFAULT PRIVILEGES … FOR ROLE` clause is standard Postgres, but
whether the Lakebase role model permits it from an app-granted role is untested. Verify before
depending on it, and prefer the app-owns-DDL rule, which needs none of this.

Isolate the capstone in **its own schema** — Free Edition allows one Lakebase project per
account, so it necessarily shares `databricks_postgres` with the support app.

## Creating the app

1. **Apps → Create app → Custom.** Confirm the account is under the **3-app** limit first; HW1
   holds one.
2. Configure the Git source: the new public repo, branch `main`. **Leave Source code path empty**
   so the repository root is used.
3. Add a resource of type **Database** → the Lakebase project, `production` branch,
   `databricks_postgres`, permission **Can connect and create**.
4. Set `ENDPOINT_NAME` in `app.yaml` to
   `projects/new-database/branches/production/endpoints/primary`. It identifies infrastructure
   and is not a secret.
5. Review authorizations and deploy.

**Deploy something trivial on Aug 7, before the app does anything useful.** A shell that renders
one query proves the whole chain — repo, source path, resource, role, credential rotation — while
there is still time to fix whatever it exposes.

## Spark jobs from Git

Task types supporting a remote Git source: **notebooks, Python scripts, SQL files, dbt**. In the
task's **Source** dropdown choose **Git provider**, then supply repo URL, provider, and a Git
reference (branch, tag, or commit).

- **Path is repo-relative with no leading `/` or `./`** — e.g. `jobs/ingest_hts.py`.
- **All tasks in a job resolve to the same commit.** Databricks snapshots the reference when the
  run begins.
- ⚠️ **Git-sourced tasks cannot write to workspace files.** They must write to ephemeral storage,
  volumes, or tables. This directly shapes C2.4: land raw Federal Register text in a Delta table
  or a volume, never a workspace path.
- Public repositories are documented elsewhere as needing no Git credentials, but the Jobs page
  is ambiguous and mentions configuring credentials when missing. ⚠️ **UNVERIFIED on this
  account** — resolve it with one throwaway job before Aug 8.
- Serverless is the only compute available and supports Python script tasks. Free Edition allows
  **5 concurrent job tasks**.

## Deploy and restart

Pushing does **not** deploy. Automatic GitHub deployment is Beta and requires a *private*
repository, so every deploy is manual:

1. Push to `main`.
2. Select the app → **Deploy**. If the Git reference changed, use the arrow beside Deploy →
   **Deploy using a different source**.
3. Watch the **Logs** tab. It is where startup failures are diagnosed.

`databricks apps deploy`, `start`, and `stop` exist as CLI equivalents, with
`--mode AUTO_SYNC|SNAPSHOT` on deploy.

**Apps stop 24 hours after being started, updated, or redeployed.** Restart before *any*
verification, grading, or demo. Lakebase also scales to zero, so warm it with one query before a
live demo rather than letting an executive watch a cold start.

## Verified Free Edition constraints

From the [Free Edition limitations page](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations):

| Resource | Limit |
|---|---|
| Databricks Apps | **3 per account**; run up to 24 h after start/update/redeploy |
| Lakebase projects | **1 per account**, scale-to-zero compute |
| SQL warehouses | **1**, `2X-Small` |
| AI Search endpoints | **1**, one search unit |
| Concurrent job tasks | **5 per account** |
| Model serving | Limits on active endpoints · no GPU serving · **certain models unavailable** |
| Workspace / metastore | 1 each; no account console or account-level APIs |
| Compute | Serverless only |
| App file size | 10 MB per file |

## Still needs live verification

Cheap checks, ordered by how much later pain they prevent:

- [ ] **V1 — Which serving endpoints actually exist on this account?** "Certain models not
      available" is the only statement Free Edition makes. Confirm `databricks-gte-large-en` is
      reachable, and that a chat endpoint exists for the agent. (This is C0.3; tonight's class
      may answer it. `vector(1024)` holds regardless, so the schema is not blocked.)
- [ ] **V2 — App count.** Confirm HW1's app is the only one, leaving room for the capstone.
- [ ] **V3 — Git-sourced job on a public repo without credentials.** One throwaway job settles it.
- [ ] **V4 — Cross-role grants.** Create a table as your user, query it as the app's service
      principal, and confirm both the failure and the fix. Better to see this deliberately for
      ten minutes than accidentally on Saturday.
- [ ] **V5 — `run-local` end to end** against real Lakebase, including the `--entry-point app.yaml`
      flag and `uv` availability for `--prepare-environment`.

## Sources

- [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy) — source code path, redeploy, logs
- [apps command group](https://docs.databricks.com/aws/en/dev-tools/cli/reference/apps-commands) — `run-local` flags
- [Develop apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development) — 10 MB file limit
- [Add a Lakebase resource to a Databricks App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase) — role creation, grants, `PG*` variables
- [Postgres extensions](https://docs.databricks.com/aws/en/oltp/projects/extensions) — `vector` 0.8.0
- [Lakebase Search / `lakebase_vector`](https://docs.databricks.com/aws/en/oltp/projects/lakebase-search) — why it is avoided
- [Use Git with Lakeflow Jobs](https://docs.databricks.com/aws/en/jobs/git) — Git source, paths, workspace-file limitation
- [Databricks-hosted foundation models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models) — embedding endpoints and dimensions
- [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations) — quotas
