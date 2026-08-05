# Capstone Brief

Last verified: **2026-08-05** · Due **Aug 9, 10:00 PM PT**

The build spec. Decisions here were settled in a structured brainstorming session on
2026-08-05; the reasoning is recorded so a later session does not re-derive it.

**Updated 2026-08-05 after a primary-source research pass.** All nine open questions are
resolved, the anchor filer is chosen, A2 is rejected, and B1's risk profile is corrected.
Evidence lives in `research/free-edition-ai-capabilities.md` and
`research/capstone-candidate-feasibility.md`; this file carries the decisions, those carry
the citations.

## Acceptance criteria — five mandatory components

**Authority:** the instructor's published requirements repo,
`github.com/EcZachly/databricks-ai-bootcamp-capstone` (single `README.md`). Adjudicated
as authoritative over the verbal Day 0 list on 2026-08-04. **All five required; missing
any one fails the submission.**

1. A **data pipeline in Spark**.
2. Integration with **at least one third-party API**.
3. **Processing of unstructured data** — video, audio, images, or text. A
   rows-and-columns-only dataset is an explicit fail.
4. A **Databricks App with a frontend** — clickable and interactive, not a notebook.
5. An **AI agent "that does stuff"** — tools that both search/retrieve **and take real
   write actions** against the data. Read-only fails regardless of tool count.

**Structurally implied but not its own bullet:** every published project idea assumes
Lakebase relational tables + embeddings over unstructured text for semantic retrieval +
an agent with read/write tools. **Vector search / RAG is therefore effectively
mandatory** as the mechanism satisfying component 3.

**Not a requirement:** CDF → Delta. Stated verbally at Day 0 as a sixth component, absent
from the published spec, and superseded. It also cannot be demonstrated on Free Edition —
it needs a Unity Catalog catalog backed by external storage, which appeared to require
its own cloud account. Optional inclusion only; not worth engineering around.

## Decisions

| Decision | Outcome |
|---|---|
| Idea space | **A custom project, distinct from the instructor's five example ideas** |
| Win condition | **Swing for top-3** — certification is the floor, not the goal |
| Ranking | **A1 primary, B1 fallback** — they share ~60% of the build |
| Gate | **None.** Research both in parallel so a pivot needs no backtracking |
| A1 data grounding | Top of the model cited from a real public manufacturer's 10-K; component tier modeled |
| Tests | A first-class deliverable — explicitly named in the top-3 judging criteria |

The five published example ideas were **movie night planner, trip/outdoor activity
planner, research & learning copilot (the instructor's own recommendation, OpenAlex API),
stock market research, and job hunting copilot**. Building a distinct project is
deliberate: the demo needs a business narrative a canned educational exercise cannot
carry. The repo explicitly permits any project.

## Candidate A1 — Tariff & Trade-Policy Exposure Copilot *(primary)*

*"What did the Federal Register just do to my COGS?"*

**The decision the agent makes:** a policy notice publishes; which purchased components
just became more expensive, and does the buyer re-price, re-source, or pre-buy?

- **Unstructured corpus:** long-form regulatory and legal text — Federal Register
  notices, trade rulings. Likely the rarest RAG corpus in a ~20,000-person cohort, and
  genuinely unqueryable any other way.
- **Grounded data:** segments, product lines, named raw-material inputs, and geographies
  derived from a **real mid-cap industrial filer's 10-K** — valves, packaging machinery,
  or composites. Cited, not invented.
- **Modeled data:** the component tier, HTS codes, suppliers, country of origin, spend.
- **Free ground truth for tests:** the anchor company's own **Item 1A Risk Factors**
  typically discuss tariff exposure directly, yielding labelled assertions to unit-test
  exposure logic against. This satisfies the *tests* criterion through **data choice
  rather than effort** — the single most useful finding of the selection session.
- **Agent write actions:** raise an exposure flag · open a sourcing-review work item ·
  assign to a buyer · advance stage · log a pricing decision · add a note.
- **Why it is a platform argument:** semantically matching a 40-page legal notice to an
  HTS code on a bill of materials is not a SQL problem.
- **Single point of failure:** if Federal Register notices do not expose HTS codes in
  machine-findable form, A1 has no product — swap the corpus to EDGAR and it becomes B1
  with the spine intact.
- **Framing discipline:** present strictly as input-cost exposure. Never as policy
  commentary.

## Candidate B1 — Thesis-Driven Acquisition Screener *(fallback)*

**The decision the agent makes:** does this company fit the acquisition thesis, and what
enters the diligence queue next?

- **Unstructured corpus:** 10-K Item 1A risk factors + Item 7 MD&A — precisely the text a
  human analyst reads, so component 3 needs no bolting-on.
- **Grounded data:** real financials via SEC XBRL `frames`. Nothing invented.
- **Agent write actions:** add to pipeline · advance/reject stage · generate and store a
  diligence question list · write a **cited** memo · record thesis-fit score. Cited
  answers are explicitly called for in the instructor's own recommended spec.
- **Lowest *financial*-data risk of the set** — EDGAR is free, keyless, and stable.
  Corrected 2026-08-05: this was originally written as lowest data risk overall, which
  research disproved. It holds for XBRL and **not** for the corpus.
- **Risks:** likely the most crowded idea among finance-background participants, and
  "thesis fit" is subjective so convincing tests are harder to write.
- **The corpus is the real risk, and it is worse than A1's.** SEC publishes no section
  delimiter; inline XBRL tags numeric facts, not sections; anchor IDs are per-filing
  hashes. Measured on a real filing, "Item 1A" matched three times with **only one the
  actual heading**. A mis-sliced section raises no error — it silently corrupts the
  embedding corpus, so B1 needs its own extraction-validation step budgeted. Also expect
  revenue-tag fragmentation: roughly half of mid-cap filers report only
  `RevenueFromContractWithCustomerExcludingAssessedTax` and carry no `Revenues` fact.
  See `research/capstone-candidate-feasibility.md`.

## Rejected on research: A2 — Supplier Distress Early-Warning

**Status changed 2026-08-05.** Previously deferred as a spare-time extension on the
reasoning that it shares A1's entire relational spine and only the incoming corpus differs.
The spine claim is true but misleading — **the corpus is the expensive part**, and research
disqualified it on two independent grounds:

- **GDELT's DOC 2.0 API returns no article body**, only headline, URL, and metadata. A
  distress signal from headlines alone is thin and does not meaningfully feed component 3.
  Reaching real text means GKG CSV parsing or BigQuery, the latter requiring a second cloud
  credential outside the Databricks environment.
- **Supplier-name matching has no GDELT-provided solution.** `V2Organizations` is raw NLP
  extraction tuned to favour recall over precision, with no disambiguation, subsidiary
  linkage, or ticker resolution. Matching it to a suppliers table means hand-building fuzzy
  entity resolution with tuned thresholds — a multi-day project, not a spare-time toggle.

It survives as the "what we would build next" slide, which still suits the future-facing
framing, **provided the data limitation is stated honestly**. Strongest raw business value
of anything generated, but mid on novelty: *news → sentiment → risk score* is the most
predictable agent demo in existence. See `research/capstone-candidate-feasibility.md`.

## Ideas considered and rejected

| Idea | Why rejected |
|---|---|
| Regulatory change → product compliance | Shares A1's novel-corpus advantage, but compliance is cost-avoidance and lands soft with an executive audience focused on margin |
| Roll-up whitespace mapper | The purest vector-search showcase, but thin write actions and no human currently makes that decision |
| Freight / weather disruption router | Open-Meteo is one of the published example ideas' APIs — reads as derivative |
| Post-acquisition integration risk | Strong narrative, but **no public corpus describes integration outcomes** — the data source is fiction |

## Shared spine — build this before choosing a corpus

A1 and B1 differ only in corpus and domain model. Everything below survives a pivot
intact, which is what makes committing to a ranking safe. Grounding A1 in a 10-K enlarged
this further, since both candidates now read from EDGAR.

| Component | Note |
|---|---|
| Lakebase project + database | **Already exists** — `new-database` / `production` / `databricks_postgres`. Free Edition allows only one project, so the capstone **must share it with the support app, isolated by a separate schema** |
| Databricks App | **Corrected 2026-08-05:** a **Source code path** may name a subdirectory, which the app then treats as its top level (it cannot read files outside it); an empty path means the repository root. The earlier "root only" claim here was wrong. **Decision: the capstone gets its own public repo with the app at root** — chosen once the constraint was known to be optional. Public repo = manual `Deploy > From Git > main`, no Git credential. Automatic GitHub deployment is Beta and **requires a private repository** — do not expect pushes to auto-deploy. Mechanics in `capstone-app-runbook.md` |
| App budget | Free Edition allows **3 apps**; homework 1 holds one, so the capstone is app #2 |
| Relational spine | `users`, `documents`, `document_chunks` (+embeddings), `work_items` (+stage), `work_item_events`, `notes`, `agent_actions` audit — roughly 6 of ~8 tables, identical either way |
| Parameterized Spark ingest | HTTP JSON → land raw → parse → write, with endpoint and parser as config |
| Agent tool contracts | `search_documents`, `get_entity`, `create_work_item`, `advance_work_item`, `add_note`, `write_memo` — signatures identical, only the nouns change |
| Test harness | pytest + fixtures + a fake-API fixture. Reuse the Day 1 pattern: 22 tests at the domain and repository seams with mocked database connections |
| Lakebase connection | Reuse the Day 1 solution exactly: OAuth database tokens **expire after one hour**, so the pool must generate a fresh credential per connection. `ENDPOINT_NAME` must be the `projects/.../branches/.../endpoints/...` **resource name**, not the UUID shown elsewhere in the Lakebase UI. This was the hardest part of Day 1 — do not rediscover it |

**Late-bound, needs the corpus decision:** the core entity table and its attributes, the
payload-specific parser, the scoring logic, and the frontend's specific views.

**Caveat:** the embedding / vector-search plumbing is corpus-agnostic but has never been
built before. Day 2 (Aug 5) teaches it. Any work on it before that class is a spike, not
an implementation. The *path* is now settled — `pgvector` in Lakebase, reusing the Day 1
connection pool — so the class fills in technique rather than deciding architecture.

**Vector dimension settled 2026-08-05:** every candidate embedding endpoint
(`databricks-gte-large-en`, `databricks-bge-large-en`, `qwen3-embedding-0-6b`) produces
**1024 dimensions**, so the column is `vector(1024)` regardless of which one Free Edition
turns out to expose. The schema is therefore **not** blocked on that verification. Prefer
GTE for its 8192-token window; BGE's 512-token window would force smaller chunks over
long Federal Register notices.

## Open questions — **all nine resolved 2026-08-05**

Answered by a primary-source research pass. Evidence and citations live in
`research/free-edition-ai-capabilities.md` (1–3) and
`research/capstone-candidate-feasibility.md` (4–9). Summaries only below; do not re-derive.

**Blocking both candidates:**

1. **Vector search — both paths work.** Mosaic Vector Search was *renamed* **Databricks AI
   Search**, not withdrawn; Free Edition grants 1 endpoint, Delta Sync index type only
   (Direct Vector Access unsupported). Independently, **Lakebase supports `pgvector`**
   (extension `vector`, hnsw/ivfflat, no preview gating). "Lakebase search" is a *third*,
   Beta feature provisioning `lakebase_vector` + `lakebase_text` (BM25) — enabling it
   restarts all project computes and is **irreversible**.
   **Decision: `pgvector` is the committed path**; AI Search is a stretch goal only.
2. **Agent write tools — yes, via the App.** UC-function writes are permitted only by
   absence of a stated restriction, and Agent Bricks' regional availability is unverified.
   The documented path is a Python agent loop inside the Databricks App writing through the
   app service principal's Lakebase credential. **Decision: hand-rolled tools in the App.**
3. **Spark — real Spark.** DataFrame API and `spark.sql` with Delta/UC writes, schedulable
   as Jobs. Constraints: **Spark Connect only, no RDD API**, no `.cache()`/`.persist()`/
   `.checkpoint()`, 5 concurrent job tasks per account. Component 1 is satisfiable.

**A1-specific:**

4. **Federal Register — YES, HTS codes are machine-findable.** The A1 single point of
   failure is cleared. Verified in live documents (`2026-15975`, `2026-15220`, `2026-15181`);
   the reliable pattern is Commerce/ITA **"Scope of the Order"** boilerplate. Volume is
   ~30–40 HTS-bearing documents/month, steady. `/documents.json` is metadata only — body
   text comes from `raw_text_url` / `full_text_xml_url`. **Constraint:** exhaustive annexes
   are often published as page images with no text layer, so **A1 is scoped to
   scope-description matching, not annex line-item coverage.**
5. **HTS schedule — solved.** `hts.usitc.gov/reststop/exportList` returns all 35,789 records
   keyless in ~12s. **Chapter 99 codes are duty *modifiers* that stack** on a base
   classification, matched by free-text scope description rather than a structured join —
   which is the "not a SQL problem" argument. DataWeb is the wrong tool (account + MFA,
   returns trade statistics).
6. **Anchor filer — CHOSEN: Mueller Water Products (MWA), CIK 1350593.** Selected over
   Gorman-Rupp's simpler single-segment structure because its Item 1A and MD&A carry
   **quantified** tariff impact, which converts directly into test assertions. Carries two
   modelling consequences: **two segments**, and a **fiscal year ending 09-30** that must
   not be aligned naively against calendar-quarter data.

**B1-specific:**

7. **EDGAR — keyless, 10 req/s, descriptive User-Agent mandatory** (bare requests 403).
   Prefer the nightly bulk ZIPs over per-CIK looping. **Item 1A / Item 7 are NOT cleanly
   delimited** — no section markers, inline XBRL tags numeric facts only, anchor IDs are
   per-filing hashes. This is B1's real risk; see the corrected B1 section above.
8. **XBRL concepts — revenue tagging is fragmented.** Safe to screen on: `NetIncomeLoss`,
   `OperatingIncomeLoss`, `Assets`, `StockholdersEquity`, `CashAndCashEquivalents…`,
   `LongTermDebtNoncurrent`, `EarningsPerShareDiluted`, `GrossProfit`. Revenue requires
   coalescing two tags. The `srt` taxonomy is absent entirely.

**A2:**

9. **Rejected.** The DOC API returns no article body, and supplier-name matching needs a
   hand-built entity-resolution layer. See the rejected-on-research section above.

### Newly opened by this research

- Free Edition also caps **1 SQL warehouse** and **1 AI Search endpoint** — the latter is
  a scarce, single, non-reusable resource, which is part of why `pgvector` wins.
- `www.sec.gov` and `www.usitc.gov` have **opposite** bot rules: SEC 403s *without* a
  descriptive User-Agent, USITC 403s *with* a browser-like one. Do not commit a real
  personal or employer address in the SEC header — this repository is public.
- Federal Register plain text is **hard-wrapped mid-sentence**; normalise whitespace before
  phrase matching or regexes silently return nothing.
- Optional enhancement worth ~half a day: `modifications_to_hts` provides an
  **HTS revision ↔ Federal Register document ↔ legal authority** join key.

## Time budget

Roughly **3.5 days**: Aug 5 (evening class), Aug 6, Aug 7 (evening class), and the weekend
to the Sunday 10:00 PM PT cutoff. Estimate for a top-3 swing including tests: **16–20
hours** against the instructor's 10-hour baseline for the already-skilled.
