# Delivery Plan

Last updated: **2026-08-06** · Hard cutoff **Aug 9, 10:00 PM PT** = **Aug 10, 12:00 AM CT**

The execution checklist. `bootcamp.md` says what the program is, `capstone-brief.md` says what
to build; this file says **what to do next, in what order, and whether it is done**. It is the
single source of truth for status — update it at the end of every work block, before pushing.

## The strategy this plan is built around

**Submit early and grind the score.** Resubmissions are unlimited, only the last one before the
cutoff counts, and the AI grader returns per-component subscores with named deductions in 1–2
minutes. That turns the grader into a free feedback loop — but only for work that exists before
Sunday. The plan is therefore shaped to reach **M1 (first scoring submission) by Saturday
evening** with all five components present even if thin, leaving Sunday entirely for
grader-driven iteration.

The failure mode to avoid is a polished 80%-complete build that has never been scored. A thin
submission that satisfies all five components beats a beautiful one missing component 5.

## Deadline structure

| When | What | Notes |
|---|---|---|
| Aug 5, 7–9 PM CT | **Day 2 class** — context engineering, vectorization, Spark pipelines, scheduling | Teaches the one thing never built before |
| Aug 6, morning | **HW2 drops** | Certification gate — non-negotiable |
| Aug 7, 7–9 PM CT | **Day 3 class** — AI agents on AgentBricks | May affect the hand-rolled-agent decision |
| Aug 8, morning | **HW3 drops** | Collides with the capstone endgame. Budget it, do not absorb it |
| **Aug 8, evening** | **M1 — first scoring capstone submission** | Self-imposed. The most important date here |
| Aug 9, 8:00 PM CT | **Personal final-submission cutoff** | 4 hours of margin against the real cutoff |
| Aug 10, 12:00 AM CT | Real cutoff. No extensions, **no time-zone adjustments** | |

Certification requires **all three homeworks *and* the capstone**. A brilliant capstone with a
missed HW3 certifies nothing.

## Deliverable inventory

| # | Deliverable | Owner deadline | State |
|---|---|---|---|
| D1 | Homework 1 — Lakebase support app | Aug 4 | ✅ **Submitted, 100/100.** `submissions/homework-1/` |
| D2 | Homework 2 — Weather Intelligence | Aug 6 | ✅ Built, deployed, live pipeline verified, submission packaged |
| D3 | Homework 3 | Aug 8 | ⬜ Not dropped |
| D4 | Capstone — A1 Tariff & Trade-Policy Exposure Copilot | Aug 9 | 🔄 Spec complete, build not started |
| D5 | Written platform pros/cons assessment (employer) | After Aug 9 | ⬜ Evidence logging starts now, see P1 |
| D6 | Five-minute executive demo (employer) | After Aug 9 | ⬜ Falls out of D4 if the frontend is built for it |

D5 and D6 are the deliverables that actually matter per `bootcamp.md`. They are cheap if
evidence is captured during the build and expensive if reconstructed afterward.

## The grading contract — check before every submission

The five mandatory components from the instructor's requirements repo. **Missing any one fails
the submission regardless of quality elsewhere.** Each row names the specific artifact that
satisfies it, so "is it done" is answerable rather than arguable.

| # | Required component | Satisfied by | Done |
|---|---|---|---|
| 1 | Data pipeline in Spark | Parameterized ingest jobs: HTS schedule + Federal Register (C2.3, C2.4) | ⬜ |
| 2 | At least one third-party API | Three: Federal Register, USITC HTS, SEC EDGAR | ⬜ |
| 3 | Processing of unstructured data | Federal Register notice bodies → chunks → embeddings → pgvector (C3.1) | ⬜ |
| 4 | Databricks App with an interactive frontend | Streamlit app #2 — exposure dashboard, notice detail, work-item queue, agent chat (C3.3, C4.3) | ⬜ |
| 5 | AI agent that **searches AND writes** | Agent loop with `search_documents` + write tools, audited to `agent_actions` (C4.1) | ⬜ |

Component 5 is the one most likely to be under-delivered under time pressure. **Read-only
fails.** A single working write tool clears the bar; zero does not.

Not required: CDF → Delta. Ignore it unless everything else is finished.

---

## Phase 0 — Tonight, before the Day 2 class (Aug 5, ~2 hrs)

Unblocking work only. Everything here is cheap and everything here changes the shape of the
build if it comes back wrong — which is exactly why none of it should wait.

**A wayfinder pass on 2026-08-05 closed C0.1 and C0.2 from first-party docs and produced
`capstone-app-runbook.md`** — repo layout, the local `run-local` loop, Lakebase role mechanics,
Git-sourced jobs, and the deploy/restart procedure. Read it before the first build session; it
exists so Aug 6–9 is spent on the product rather than on platform archaeology.

- [x] **C0.1 — RESOLVED by the wayfinder pass.** The root-only constraint does not exist: Apps
      accept a **Source code path** naming a subdirectory. The brief's claim was wrong and is
      corrected. **Decision: the capstone gets its own public repository with the app at root** —
      taken as an informed choice, not a forced one.
- [x] **C0.2 — Superseded by the wayfinder pass.** App budget confirmed fine (3 apps, HW1 holds
      one). The real risk was not the count but **Postgres role ownership** across a second app,
      the Spark jobs, and local dev — see the identity trap in `capstone-app-runbook.md`. Live
      checks moved to V1–V5 below.
- [~] **C0.3 — Partially resolved; no longer blocking.** All candidate embedding endpoints are
      **1024-dimension**, so the schema is `vector(1024)` regardless and C2.1 can proceed. What
      remains is *which* endpoints this account actually exposes — tracked as **V1**, expected
      from tonight's class. Record the answer in `research/free-edition-ai-capabilities.md`.
- [x] **C0.6 — DONE.** `github.com/cookx775/tariff-copilot` (public), cloned to
      `/Volumes/Crucial X9/tariff-copilot`, identity set, `git push --dry-run` verified on a real
      ref update before any code, then pushed for real. Remote author confirmed as
      `cookx775@users.noreply.github.com`. Only `.gitignore` is committed.
- [ ] **V1–V5 — Live verification checklist** in `capstone-app-runbook.md`. All cheap; V4
      (cross-role grants) is the one that prevents a Saturday `permission denied` hunt.
- [ ] **C0.4 — Snapshot the HTS schedule.** Call `hts.usitc.gov/reststop/exportList`, confirm
      the keyless ~12s / 35,789-record behaviour still holds, and save the payload locally so no
      later build block is blocked on USITC availability. Remember the inversion: **USITC 403s
      *with* a browser-like User-Agent**, SEC 403s *without* a descriptive one.
- [ ] **C0.5 — Snapshot the Federal Register samples.** Pull the three verified documents
      (`2026-15975`, `2026-15220`, `2026-15181`) via `raw_text_url`. Confirm the "Scope of the
      Order" pattern and the **hard-wrapped mid-sentence** whitespace problem. These become the
      parser's test fixtures — no live API call in the test suite.

## Phase 1 — Day 2 class (Aug 5, 7–9 PM CT)

- [ ] Attend. Capture the vectorization and job-scheduling technique.
- [ ] **Note anything that contradicts the `pgvector` decision or the hand-rolled-agent
      decision.** The architecture is settled; the class fills in technique. If it genuinely
      contradicts a decision, amend `capstone-brief.md` — do not silently diverge.

## Phase 2 — Aug 6 (HW2 + foundation, ~6 hrs)

- [x] **D2 — Homework 2.** Standalone Flask source under `homework-2/`, reusing the Day 1 App
      resource through its source-code path. Direct `psycopg2` document/vector writes replace the
      lab's failed Spark/JDBC route. Deployed to `ai-support-app`; synced 28 Chicago/Austin
      documents, inserted 28 vectors, verified ranked cosine search plus the live HNSW/FK/vector
      schema, and packaged the evidence under `submissions/homework-2/`.
- [ ] **C2.1 — Capstone schema DDL.** Own schema in the shared Lakebase project (one project per
      account, so isolation is by schema). Relational spine — `users`, `documents`,
      `document_chunks` (+ vector column), `work_items` (+ stage), `work_item_events`, `notes`,
      `agent_actions` — plus the A1 domain: segments, product lines, components/BOM, suppliers,
      country of origin, HTS codes, spend. Enable the `vector` extension and create the hnsw
      index. **Commit as a `.sql` file** — the submission ZIP must contain table DDLs.
- [ ] **C2.2 — Domain + repository layer.** Mirror the `support_app/` structure. **Reuse
      `support_app/db.py` verbatim** — OAuth tokens expire after one hour so the pool generates a
      fresh credential per connection, and `ENDPOINT_NAME` must be the
      `projects/.../branches/.../endpoints/...` resource name. This was the hardest part of Day 1;
      copy it, do not rewrite it.
- [ ] **C2.3 — Spark ingest: HTS schedule** → Delta → Lakebase.
- [ ] **C2.4 — Spark ingest: Federal Register.** Land raw → parse the scope description → extract
      HTS codes → chunk. **Endpoint and parser as configuration**, per the shared-spine design, so
      a corpus pivot costs a config change. Normalise whitespace before any phrase matching.
- [ ] **C2.5 — Seed the modeled tier.** BOM, suppliers, origins, and spend, grounded in Mueller
      Water Products' (CIK 1350593) real segments and named raw-material inputs. Two segments,
      **fiscal year ends 09-30** — do not align it naively against calendar quarters.
- [ ] **C2.6 — Extract test ground truth from MWA Item 1A.** The quantified tariff language is
      *why* this filer was chosen over Gorman-Rupp. Convert it into labelled assertions now, as a
      fixture. This satisfies the tests criterion through data choice rather than effort, and it
      independently validates the anchor-filer decision while there is still time to change it.
      Expect Item 1A to be **badly delimited** — "Item 1A" matched three times on a real filing
      with only one being the heading, and a mis-slice fails **silently**. Eyeball the output.

## Phase 3 — Aug 7 (retrieval + deployed shell, ~6 hrs)

- [ ] **C3.1 — Embedding pipeline.** Chunks → vectors → `pgvector`. Depends on C0.3.
- [ ] **C3.2 — Retrieval + exposure logic.** `search_documents` similarity query, then the match
      from notice scope description → HTS code → affected component → spend. Chapter 99 codes are
      duty **modifiers** that stack on a base classification and are matched by **free-text scope
      description, not a structured join** — this *is* the "not a SQL problem" argument, so it
      needs to visibly work.
- [ ] **C3.3 — Deploy the app shell as app #2.** ⚠️ **Deploy something trivial early.** Deployment
      is where the surprises live and Day 1 proved it. A shell that renders one query on Friday is
      worth more than a finished app first deployed on Sunday.
- [ ] **Day 3 class (7–9 PM CT)** — AgentBricks. Note whether it changes the decision to
      hand-roll agent tools in the App. Default is to keep the hand-rolled path: it is the
      documented one and the decision is already recorded.

## Phase 4 — Aug 8 (HW3 + agent + **M1**, ~7 hrs)

- [ ] **D3 — Homework 3.** Drops in the morning. Build and submit **before** touching the
      capstone. It is a certification gate and the capstone is not yet at risk at this point.
- [ ] **C4.1 — Agent loop and write tools.** `search_documents`, `get_component` / `get_supplier`,
      then the writes: raise an exposure flag, open a sourcing-review work item, assign a buyer,
      advance stage, log a pricing decision, add a note, write a cited memo. Every call writes to
      the `agent_actions` audit table — that table is the evidence for component 5.
- [ ] **C4.2 — Test suite.** pytest at the domain and repository seams with mocked connections
      (the Day 1 pattern, 22 tests), a fake-API fixture built from the C0.4/C0.5 snapshots, and
      the C2.6 ground-truth exposure assertions. **Tests are named in the top-3 judging criteria**
      — this is scored work, not hygiene.
- [ ] **C4.3 — Frontend views.** Exposure dashboard, notice detail with citations, work-item
      queue, agent chat. Build it to be **legible to a non-technical executive in five minutes** —
      that constraint is D6's entire deliverable, and honouring it now costs nothing.
- [ ] 🎯 **M1 — FIRST SCORING SUBMISSION.** Run the grading-contract table above. If all five
      rows are checked, zip and upload to `learn.dataexpert.io/assignment/4904`. **Ship it even if
      it is ugly.** The grader's per-component feedback is the most valuable input available for
      Sunday, and it cannot be obtained any other way.

## Phase 5 — Aug 9 (grind the score, ~5 hrs)

- [ ] **C5.1 — Work the grader feedback.** Read the deductions and improvement suggestions, fix
      the cheapest-per-point items first, resubmit. Repeat. This is the whole day's job.
- [ ] **C5.2 — Submission README and write-up.** Business problem, architecture, how each of the
      five components is satisfied, how to run the tests. Judging weighs "solves an interesting
      business problem" and "a working demo" — say so explicitly rather than leaving it inferable.
- [ ] **C5.3 — Demo evidence.** Screenshots or a short recording. **Restart the app first** — Free
      Edition apps stop 24 hours after being started, updated, or redeployed, and Lakebase scales
      to zero so the first query is slow. Restart before *any* verification, grading, or demo.
- [ ] **C5.4 — Final verification pass.** Tests green · app live and clicked through · agent
      performs a real write and the row appears in `agent_actions` · DDLs present in the ZIP · no
      credentials, tokens, or real personal/employer addresses anywhere in the archive (the SEC
      User-Agent header is the specific trap, and this repository is public).
- [ ] 🚩 **Final submission by 8:00 PM CT.** Four hours of margin. Then stop.
- [ ] Stretch, only if genuinely finished: `modifications_to_hts` as an HTS-revision ↔ FR-document
      ↔ legal-authority join (~half a day of value), or the AI Search endpoint. Both are
      explicitly optional. **Neither is worth risking a component on.**

## Phase P — Standing process items (run throughout)

- [ ] **P1 — Log platform friction as it happens.** Every workaround, undocumented behaviour,
      limit hit, and thing that should have been easier goes into
      `documentation/platform-assessment-log.md` **at the moment it occurs**. This file *is* D5.
      Written contemporaneously it is nearly free; reconstructed on Aug 10 it is a fabrication
      exercise and the specifics — the ones that make an assessment credible — are already gone.
- [ ] **P2 — Push after every meaningful chunk.** The drive is exFAT with no journaling; an
      unclean eject during a write can corrupt the working tree. GitHub is the only real backup.
- [ ] **P3 — Update this file at the end of every work block.** A stale plan is worse than none,
      because it gets trusted.

## Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| ~~Capstone app has no deploy root~~ | — | ✅ **Closed.** Subdirectory paths are supported; own repo chosen anyway |
| ~~App budget 4-against-3~~ | — | ✅ **Closed.** 3 apps, HW1 holds one |
| **Postgres role ownership across identities** | App deploys clean, then `permission denied for table` at query time | **App owns all DDL, jobs write data only.** V4 proves it deliberately. This replaced C0.2 as the real risk |
| **No embedding endpoint on Free Edition** | Degrades component 3; does **not** block the schema | V1, from tonight's class. `vector(1024)` holds either way. Fallback: local model in the Spark job |
| **10 MB app file limit** | Deploy fails late, after everything looks right | Keep the 35,789-row HTS snapshot out of the app source path — Delta table or volume only |
| **Git-sourced jobs cannot write workspace files** | Silent design constraint on C2.4 | Land raw Federal Register text in Delta or a volume, never a workspace path |
| **HW3 lands Aug 8 and eats the endgame** | Certification vs. capstone quality tradeoff | HW3 first that morning; M1 already de-risked by then |
| **Item 1A mis-slices silently** | Corrupts the embedding corpus with no error | C2.6 eyeballs output. Known: 3 matches, 1 real heading |
| **Nothing scored until Sunday** | No feedback loop, no recovery time | M1 on Aug 8. The plan's central defence |
| **24-hour app shutdown at grading time** | Grader sees a dead app | Restart immediately before every submission and demo |
| **Vector plumbing never built before** | Unknown-unknowns on the critical path | Day 2 class teaches it; architecture already decided so the class adds technique only |

## Effort check

Phase 0 ≈2 · Phase 2 ≈6 · Phase 3 ≈6 · Phase 4 ≈7 · Phase 5 ≈5 = **~26 hours**, of which
roughly 6 belong to HW2 and HW3. That leaves **~20 hours of capstone work**, at the top of
`capstone-brief.md`'s 16–20 hour estimate for a top-3 swing. It fits, with no slack. Anything
added to scope must displace something, and the first things to cut are the Phase 5 stretch
items — never a component in the grading contract.

## Status log

Append one line per work block. Newest last.

- **2026-08-05** — Plan created. Capstone spec complete, all nine research questions resolved,
  build not started. Three verification items raised for tonight (C0.1 deploy root, C0.2 app
  budget, C0.3 serving endpoints); C0.1 is a potential hard blocker on component 4.
- **2026-08-05** — Wayfinder pass on the capstone app lifecycle; `capstone-app-runbook.md` added.
  C0.1 closed (subdirectory paths *are* supported — the brief was wrong; own repo chosen anyway),
  C0.2 closed and replaced by the Postgres role-ownership risk, C0.3 downgraded from blocking
  (all embedding endpoints are 1024-dim, so C2.1 can start). Found: `run-local` defaults to
  `app.yml` not `app.yaml`; 10 MB per-app-file limit; Git-sourced jobs cannot write workspace
  files. Next: C0.6 create the repo, then V1–V5.
- **2026-08-05** — C0.6 closed. `cookx775/tariff-copilot` created public, cloned as a sibling on
  this drive, commit identity set, push path proven by `git push --dry-run` on a real ref update
  *before* any code. Repo holds `.gitignore` only. Found: cloning onto exFAT prints
  `error: non-monotonic index` because macOS writes an AppleDouble `._pack-*.idx` twin that git
  parses as a pack index — the clone still succeeds and `git fsck` is clean; `find . -name '._*'
  -delete` clears it. Documented in the runbook so it is not mistaken for corruption mid-build.
  Next: V1–V5 live verification, then C0.4/C0.5 snapshots.
- **2026-08-06** — Homework 2 spec received. Built the isolated Weather Intelligence Flask app,
  NWS/Nominatim harvester, Lakebase `vector(384)` schema, direct-psycopg2 embedding job, cosine
  search endpoint, and local test suite. Reuses the existing App slot; live deployment and
  evidence capture remain before submission.
