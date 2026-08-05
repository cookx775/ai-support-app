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
