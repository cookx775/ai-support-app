# The Bootcamp

Last verified: **2026-08-05**

Data Expert's free **"Rise of the AI Data Engineer"** cohort. Instructor **Zach Wilson**
(Data Expert founder); Databricks is the cohort's major sponsor. Runs entirely on
**Databricks Free Edition** — permanent, not a trial.

## Why I am doing this

Hands-on preparation for an employer platform evaluation, with a written pros/cons
assessment owed at the end. The certificate is secondary; the **capstone artifact and
the written assessment are the outputs that matter.**

The finished capstone will be demonstrated to executive leadership as a
**platform-capability argument** — "here is what this platform does end to end, and here
is the shape of thing we would pursue in future" — not as a product pitch. Two
consequences for design:

1. The build should exercise capability the incumbent BI stack cannot deliver today.
   Vector search over embedded long-form text, plus an agent writing back to an OLTP
   store, is that seam.
2. The demo must be legible to a non-technical executive in about five minutes.

A secondary thesis being tested: whether AI-assisted content can take someone from zero
to a working lakehouse app in a week. This cohort is a controlled test of exactly that,
with a measurable outcome.

> No employer data is used anywhere. Everything runs on a personal Free Edition account
> against public third-party APIs. See the sensitivity rule in `documentation/README.md`.

## Schedule

| Item | Detail |
|---|---|
| Live classes | **Aug 3, 5, 7** — 5:00–7:00 PM PT, 2 hrs each; recorded and posted same day |
| Day 1 (Aug 3) | Lakebase (Postgres) + Databricks Apps + CDF → Delta |
| Day 2 (Aug 5) | Context engineering, vectorization, Spark pipelines + scheduling |
| Day 3 (Aug 7) | AI agents on AgentBricks |
| Homework | 3 assignments, dropping the morning after each lecture (Aug 4 / 6 / 8) |
| Capstone | Due **Aug 9, 10:00 PM PT** — no extensions, **no time-zone adjustments** |

## Certification

Requires passing **all three homework assignments *and* the capstone**. Reward is a
certificate plus access to a private Discord channel for the certified cohort — framed
by the instructor as the real prize.

Cohort scale: ~20,000 signups across 181 countries. The instructor expects **under 1%**
to certify. Effort estimate: **~10 hours if already skilled, 15–20 if new to data.**
Individual work only; group submissions are not allowed.

## Rewards beyond certification

- **Top 3 individual projects:** a free seat in the paid bootcamp (~$2,500 value), or a
  personal LinkedIn recommendation to the instructor's ~500,000 followers.
- Winners announced roughly **Aug 10–11**. Top projects are picked **by hand** after AI
  grading.
- **Judging criteria for "top":** overall quality, **tests**, whether it solves an
  interesting business problem, and a working demo.

## Submission mechanics

- **Zip-file upload** to `learn.dataexpert.io` — GitHub repo submissions are explicitly
  **not** accepted. The zip should contain table DDLs, Python code, everything.
- Capstone target: `learn.dataexpert.io/assignment/4904`.
- **AI-graded in ~1–2 minutes**, scored out of 100 with per-component subscores,
  strengths, deductions, and improvement suggestions. Prompt injection is checked for.
- **Unlimited resubmissions** — only the last submission before the cutoff counts. This
  rewards submitting something early and grinding the score up.

## Instructor's stated framing

Worth knowing because it is what the hand-judging rewards:

- *"The business value matters more than the data size."*
- **Data modeling** is named the most durable skill; hand-writing SQL and pipelines is
  the part already being automated.
- The target capability: *"Can we build data pipelines that feed AI agents that then make
  automatic business decisions?"*
- On becoming hard to replace: *"understand the business, learn who makes which
  decisions and on what context, then capture that context well enough that an agent can
  make the same decision."*

A useful inversion follows from this: **inventing a clean relational model is an asset,
not a liability.** A well-modeled synthetic core scores with this instructor.

## Platform constraints that shape every assignment

Verified against first-party documentation — see
`documentation/research/databricks-free-edition-app-foundation.md` for citations.

- **One Lakebase project per Free Edition account.** Every app must share it, isolated by
  schema. The existing project is `new-database`, branch `production`, database
  `databricks_postgres`.
- **Three Databricks Apps maximum.** Homework 1 holds one; the capstone needs one; one
  spare.
- **Apps stop automatically 24 hours** after being started, updated, or redeployed. They
  can be restarted — do so immediately before any verification, grading, or demo.
- **Serverless compute only**; no custom compute configuration. Fair-use quotas apply.
- Lakebase **scales to zero**, so the first query after an idle period takes several
  seconds.

## Assignment index

**Live status, sequencing, and blockers live in `delivery-plan.md`** — that file is
authoritative. This table only maps assignments to their durable records.

| Assignment | Dropped | Durable record |
|---|---|---|
| Homework 1 — Lakebase-backed support app | Aug 4 | `submissions/homework-1/` |
| Homework 2 — Weather Intelligence vector search | Aug 6 | `homework-2/` and `submissions/homework-2/` |
| Homework 3 — Weather Prediction MCP + Agent | Aug 8 | `homework-3/` and `submissions/homework-3/` |
| Capstone | — | `documentation/capstone-brief.md` |

Homework 2 is standalone application source under `homework-2/`. It reuses the existing
Databricks App resource through its source-code-path setting, preserving the Day 1 source while
avoiding another app allocation.
