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
