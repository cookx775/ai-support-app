# Documentation

Durable context for this bootcamp workspace. Read this first; it says what lives where
and what must never be written here.

**Starting a work session?** Go to [`delivery-plan.md`](delivery-plan.md) — it holds the
task checklist, the current phase, and what is blocking.

## Why this layer exists

This drive moves between machines. A separate personal knowledge base holds the
narrative and stakeholder context, but it lives on one machine only, so any build
session on another machine used to start with no foundation — no statement of what the
bootcamp is, why it is being done, or what the capstone has to satisfy. This layer
fixes that. It is written to be sufficient on its own.

## What belongs where

| Path | Holds | Rule |
|---|---|---|
| `documentation/bootcamp.md` | Program structure, deadlines, certification bar, submission mechanics | Facts about the course |
| `documentation/capstone-brief.md` | Capstone acceptance criteria, candidate designs, shared architecture, open questions | The build spec |
| `documentation/delivery-plan.md` | Task checklist, sequencing, milestones, risk register, status log | **The single source of truth for status.** Update at the end of every work block |
| `documentation/capstone-app-runbook.md` | Capstone app mechanics: repo layout, local loop, Lakebase roles, Git-sourced jobs, deploy | Mark each fact doc-verified or ⚠️ unverified, and correct in place once executed |
| `documentation/platform-assessment-log.md` | Contemporaneous evidence for the written platform assessment | Append as friction occurs, never reconstruct afterward |
| `documentation/research/` | Verified platform findings | **First-party citations only.** Separate verified fact from project decision from local observation, and stamp `Last verified` |
| `documentation/missions/` | Per-assignment learning objectives | One file per assignment |
| `documentation/lessons/`, `reference/`, `assets/` | Teaching material written for this workspace | Relative links between them; keep them moving together |
| `submissions/homework-N/` | The graded record: ZIP, screenshots, write-up | Immutable once graded. Fix errors only |
| `homework-2/` | Standalone Weather Intelligence app, job, DDL, tests | Deployed by setting the App source-code path to this directory |
| repository root | Day 1 application source and shared workspace configuration | The Day 1 app remains deployable from root. Nothing already here may move |

## Sensitivity rule — this is a PUBLIC repository

Nothing committed here may name the employer, its people, its financial targets, its
partners, its portfolio, or any internal strategy. Committing to a public repository is
irreversible: it is cached, indexed, and forked, and deleting a file later does not
undo it.

This costs nothing, because the material that is confidential is material a build
session never needs. State the framing generically and it stays fully useful:

> Undertaken as hands-on preparation for an employer platform evaluation, with a
> written pros/cons assessment owed at the end. The finished build will be demonstrated
> to executive leadership as a **platform-capability argument** — "here is what this
> platform does end to end, and here is the shape of thing we would pursue" — rather
> than as a product pitch. The business problem should therefore land on input-cost /
> margin exposure or on acquisition screening, and should exercise capability the
> incumbent BI stack cannot deliver today.

That paragraph is the entire narrative a build needs. Names, figures, dates, and
stakeholder specifics stay out.

## Direction of flow

One-way, to avoid two competing sources of truth over the same facts:

- **This drive is authoritative** for platform facts, API behaviour, schema, code,
  tests, and build decisions.
- **The personal knowledge base is authoritative** for narrative, stakeholder framing,
  and how this connects to other work.
- At milestones, insights derived here are carried **drive → knowledge base**, on the
  machine where that base lives. Never the reverse.

## Learning artifacts

| Assignment | Mission | Full lesson | Printable checklist |
|---|---|---|---|
| Homework 1 — Lakebase support app | [`missions/homework-1-recreate-lakebase-app.md`](missions/homework-1-recreate-lakebase-app.md) | [`lessons/0001-recreate-lakebase-support-app.html`](lessons/0001-recreate-lakebase-support-app.html) | [`reference/databricks-app-recreation-checklist.html`](reference/databricks-app-recreation-checklist.html) |
| Homework 2 — Weather Intelligence | [`missions/homework-2-weather-intelligence.md`](missions/homework-2-weather-intelligence.md) | [`lessons/0002-weather-intelligence-vector-search.html`](lessons/0002-weather-intelligence-vector-search.html) | [`reference/weather-intelligence-pipeline-checklist.html`](reference/weather-intelligence-pipeline-checklist.html) |

## Working on a machine for the first time

**The drive is portable; git credentials are not.** Every new machine needs a one-time
GitHub authentication before it can push, and the failure mode is confusing: the commit
identity (`cookx775@users.noreply.github.com`) lives in this repository's config and
travels with the drive, so local commits look correct while `git push` is rejected with
`403 Permission denied` — often naming a *different* GitHub account that happens to be
authenticated on that machine.

Identity and authorization are separate. Before the first push on a new machine:

```bash
gh auth login --hostname github.com --git-protocol https --web   # choose cookx775
gh auth switch --hostname github.com --user cookx775
gh auth setup-git
```

`gh auth setup-git` is not optional if the machine's credential helper is
`osxkeychain` — it will otherwise keep handing git a stale token for whichever account
was there first. Verify with `gh auth status` and a `git push --dry-run`.

## Backup

The drive is **exFAT** — no journaling, so an unclean eject during a write can corrupt
the working tree. Git on GitHub is the only real backup, which is why submission ZIPs
and screenshots are tracked rather than ignored. Push after every meaningful chunk of
work, not at the end of the day.
