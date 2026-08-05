# Capstone Brief

Last verified: **2026-08-05** · Due **Aug 9, 10:00 PM PT**

The build spec. Decisions here were settled in a structured brainstorming session on
2026-08-05; the reasoning is recorded so a later session does not re-derive it.

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
- **Lowest data risk of the set** — EDGAR is free, keyless, and stable.
- **Risks:** likely the most crowded idea among finance-background participants, and
  "thesis fit" is subjective so convincing tests are harder to write.

## Deferred: A2 — Supplier Distress Early-Warning

Shares A1's entire relational spine; only the incoming corpus differs (distress news via
GDELT vs. policy text). Model it as a second `threat_source` type and populate it **only
if there is spare time**. Otherwise it becomes the "what we would build next" slide,
which suits the future-facing framing.

Strongest raw business value of anything generated, but mid on novelty: *news → sentiment
→ risk score* is the most predictable agent demo in existence.

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
| Databricks App | Deploys from the **root of a Git repository**. Public repo = manual `Deploy > From Git > main`, no Git credential. Automatic GitHub deployment is Beta and **requires a private repository** — do not expect pushes to auto-deploy |
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
an implementation.

## Open questions — resolve before building the late-bound half

**Blocking both candidates, highest priority:**

1. What is the actual embedding / vector-search path on **Free Edition**? Is Mosaic Vector
   Search available, or must embeddings come from a foundation-model endpoint with vectors
   stored in Lakebase (pgvector)? What did enabling "Lakebase search" on Day 1 provision?
2. Can an **AgentBricks** agent on Free Edition be given custom **write** tools, and how
   are they registered? Day 3 (Aug 7) covers this.
3. Is Spark usable meaningfully for ingest on serverless Free Edition, or does the
   pipeline collapse into notebook Python? Component 1 requires "a pipeline in Spark."

**A1-specific:**

4. Does the **Federal Register API** expose full notice text, and do HTS codes appear in
   machine-findable form? Which agencies and document types carry them (USTR,
   Commerce/ITA, CBP, USITC)? What monthly volume?
5. Is there a free API for the **HTS schedule itself** (USITC HTS / DataWeb, or the
   published export files) to map code → description → duty rate?
6. Which **real mid-cap industrial filer** is the best anchor? Criteria: single-ish
   segment, named raw-material inputs in Item 1/1A, explicit tariff discussion in Risk
   Factors, recent 10-K. **Unchosen — this is the last design decision before the domain
   model can be written.**

**B1-specific:**

7. **SEC EDGAR** full-text search + XBRL `frames`: rate limits, the User-Agent header
   requirement, and whether Item 1A / Item 7 are cleanly delimited or must be parsed
   heuristically.
8. Which XBRL financial concepts are reliably populated across mid-cap filers — what can
   a thesis screen actually filter on?

**A2, only if cheap:**

9. GDELT 2.0 DOC API shape, and whether supplier-name matching is tractable without an
   entity-resolution layer.

## Time budget

Roughly **3.5 days**: Aug 5 (evening class), Aug 6, Aug 7 (evening class), and the weekend
to the Sunday 10:00 PM PT cutoff. Estimate for a top-3 swing including tests: **16–20
hours** against the instructor's 10-hour baseline for the already-skilled.
