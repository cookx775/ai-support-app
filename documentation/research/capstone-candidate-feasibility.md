# Capstone Candidate Data-Source Feasibility

Last verified: **2026-08-05**

This note answers open questions 4–9 of `../capstone-brief.md` — the data-source questions
that decide whether each capstone candidate is buildable. Platform capabilities (vector
search, agent write tools, Spark) are in `free-edition-ai-capabilities.md`.

Every claim below was checked by fetching the live endpoint or document. Sources are
government APIs and filings rather than Databricks documentation, so "first-party" here
means the agency that owns the data.

## Headline verdicts

| Candidate | Verdict | Basis |
|---|---|---|
| **A1** — Tariff & Trade-Policy Exposure Copilot | **GO**, with a scoping constraint | HTS codes confirmed present in machine-readable notice text |
| **B1** — Thesis-Driven Acquisition Screener | Viable fallback, but **riskier than the brief assumes** | XBRL is solid; 10-K narrative extraction is the riskiest parse of the set |
| **A2** — Supplier Distress Early-Warning | **Rejected** | The news API returns no article body, and supplier matching needs its own entity-resolution layer |

## Two opposite bot-defence rules — read this before writing any fetch code

These agencies behave in **opposite** ways. Applying the wrong rule produces an immediate
403 that looks like an outage.

| Host | Rule |
|---|---|
| `www.sec.gov`, `data.sec.gov` | **Must** send a descriptive `User-Agent` containing an organisation name and contact email. Bare or default clients get 403 |
| `www.usitc.gov` | **Must not** send a browser-like `User-Agent`. A bare client string returns 200; an impersonated Chrome or Googlebot string returns 403 |
| `hts.usitc.gov/reststop` | No bot defence observed; plain clients work |
| `www.federalregister.gov` | Bot check guards the human-facing HTML pages only. `/api/v1/*.json` and the full-text endpoints respond to plain clients |

**Do not commit a real personal or employer email address in the SEC User-Agent string.**
This repository is public and `../README.md` forbids naming the employer. Use a generic
project contact. The header format SEC documents is an organisation name followed by a
contact address:

```
User-Agent: DatabricksBootcampCapstone research-contact@example.com
```

[SEC: Accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

## Q4 — Federal Register: do notices expose HTS codes? **Yes.**

This was the identified single point of failure for A1. It is resolved.

### Verified: HTS codes appear as literal strings in machine-readable text

- Presidential proclamation **2026-15975** (published 2026-08-05, 91 FR 50645) contains:
  "classifiable in the Harmonized Tariff Schedule of the United States (HTSUS) in
  subheadings 6810.99.0020, 6810.99.0040, and 7020.00.6000." Present in both the plain-text
  and XML renditions, not only in a search excerpt.
  [Document 2026-15975](https://www.federalregister.gov/documents/2026/08/05/2026-15975)
- Commerce/ITA antidumping duty order **2026-15220** (2026-07-28) contains: "classifiable
  under Harmonized Tariff Schedule of the United States (HTSUS) subheadings 2916.12.5050,
  2916.14.2050, 3824.99.2900, 3907.29.0000 and 3907.30.0000."
  [Document 2026-15220](https://www.federalregister.gov/documents/2026/07/28/2026-15220)
- USTR Section 301 notice **2026-15181** (2026-07-28) lists individual products by subheading
  inline in prose. [Document 2026-15181](https://www.federalregister.gov/documents/2026/07/28/2026-15181)

The reliable pattern is the **"Scope of the Order"** boilerplate, near-universal across
Commerce/ITA antidumping and countervailing duty initiations, determinations, orders, and
continuations. Those paragraphs state the HTSUS subheadings and carry the standard
disclaimer that the written scope description is dispositive.

### The `raw_text_url` output is hard-wrapped — normalise whitespace before matching

Confirmed while re-verifying document 2026-15220: the plain-text rendition is wrapped at
roughly 72 characters, and **the wrap falls inside the sentence and between the codes**:

```
    This merchandise is currently classifiable under Harmonized
Tariff Schedule of the United States (HTSUS) subheadings
2916.12.5050, 2916.14.2050, 3824.99.2900, 3907.29.0000 and
3907.30.0000. Subject merchandise may also be entered under
subheadings 2916.12.1000 and 3824.99.9397.
```

A phrase regex such as `classifiable under Harmonized Tariff Schedule...` therefore matches
**nothing**, while an HTS-code pattern still matches because individual codes are not split.
Two consequences for the parser: collapse newlines and runs of whitespace to single spaces
before any phrase-level matching, and prefer the XML rendition, whose `<FP>` elements carry
the paragraph as a unit. This is a silent-failure mode — the fetch succeeds and the regex
simply returns nothing.

### Verified API mechanics

- Keyless. "FederalRegister.gov APIs do not require API keys."
  [FR API documentation](https://www.federalregister.gov/developers/documentation/api/v1)
- `/documents.json` returns **metadata only**. Body text comes from separate per-document
  URLs exposed as fields: `raw_text_url` (.txt), `full_text_xml_url` (.xml), and
  `body_html_url` (.html). The XML is the better chunking input because it preserves
  semantic boundaries (`<FP>`, `<HD>`, `<GPOTABLE>`).
- The document-type enum is **`RULE`, `PRORULE`, `NOTICE`, `PRESDOCU`**. It is `PRORULE`,
  not `PROPOSED_RULE`; the wrong value returns zero results rather than an error.
- Search conditions include `conditions[term]`, `conditions[agencies][]`,
  `conditions[type][]`, `conditions[publication_date][gte|lte|is|year]`,
  `conditions[docket_id]`, and `conditions[topics][]`.
- `per_page` maximum is **1000**. Requesting `page * per_page > 10000` returns HTTP 400
  with "Pagination limit exceeded". The `count` field is exact for narrow queries but
  plateaus at 10,000 for broad ones — read values at 10,000 as "at least 10,000".

### Verified volume

Trailing 12 months to 2026-08-05, documents mentioning "HTSUS" literally:

| Agency | Documents/year | Approx/month |
|---|---|---|
| International Trade Administration (Commerce) | 313 | ~26 |
| International Trade Commission | 32 | ~2.7 |
| Customs and Border Protection | 29 | ~2.4 |
| USTR | 19 | ~1.6 |
| Presidential documents | 23 | ~2 |

ITA month-by-month counts for Feb–Jul 2026 were 36, 33, 26, 31, 25, 34 — steady, no
seasonality. Roughly **30–40 HTS-bearing documents per month** across these sources.

### The constraint that must shape the product

Large annex-style exhaustive HTS line lists are **frequently published as page images with
no text layer**. Verified on USTR document **2026-14542** (2026-07-20, 100 printed pages):
Annex II — the line-by-line list of covered subheadings, roughly 85 of the 100 pages —
exists in no text rendition. The `.txt` contains 86 occurrences of
`[GRAPHIC] [TIFF OMITTED]`, the XML has matching `<GPH><GID>` tags with no corresponding
text, and the HTML embeds 86 `<img>` elements.
[Document 2026-14542](https://www.federalregister.gov/documents/2026/07/20/2026-14542)

This is a long-standing composition pattern for large multi-column tables, not an anomaly.

### Annex fidelity is document-dependent — an unresolved disagreement, recorded

A separate check of document **2020-03377** found that document's annex **fully present** in
`full_text_xml_url`, as a structured `<GPOTABLE COLS="5">` with real `<ENT>` cells
(for example `9903.88.40`) plus 47 prose exclusion entries carrying inline HTS numbers.
[Document 2020-03377](https://www.federalregister.gov/documents/2020/02/20/2020-03377)

Both observations are believed correct: **annex fidelity varies by document**. Some annexes
are composed as real table markup; others are page images. The practical implications:

- Parse `<GPOTABLE>`, `<ENT>`, and `<FP>` properly. Naive tag-stripping discards codes that
  are genuinely present in the XML — a real and easy bug.
- Detect `<GPH>` / `<GID>` graphic references and mark those documents **partially
  ingested** rather than letting them appear complete.
- A future session should test its own parser against **both** document numbers above before
  concluding anything about coverage.

## Q5 — HTS schedule data: solved

### Verified: the full schedule is one keyless request

```
https://hts.usitc.gov/reststop/exportList?from=0101&to=9999&format=JSON&styles=false
```

Returns the entire schedule: **35,789 records, ~12.6 MB, about 12 seconds**, with no
authentication, registration, or rate-limit wall encountered.

The response is a **flat JSON array**, not nested by chapter; `indent` (0–6) encodes nesting
depth for reconstructing the hierarchy. Fields per record:

| Field | Content |
|---|---|
| `htsno` | e.g. `8481.10.00.20` |
| `indent` | nesting level, `"0"`–`"6"` |
| `description` | classification text; header rows end in `:` |
| `superior` | category-header flag |
| `units` | e.g. `["No."]`; empty on header rows |
| `general` | general (MFN / Column 1) duty rate, e.g. `"2%"` |
| `special` | preferential rates by FTA country-group code |
| `other` | Column 2 (non-NTR) rate |
| `footnotes` | array; may cross-reference a Chapter 99 heading |
| `quotaQuantity`, `additionalDuties` | rarely populated |

Note a dead field: `addiitionalDuties` (misspelled) is always null and should be ignored.

Bulk CSV, JSON, and XLSX are also published, at
`https://www.usitc.gov/sites/default/files/tata/hts/hts_2026_revision_{N}_json.json` and
matching `_csv`/`_xls` variants. Revisions run roughly every two to three weeks — 2026
reached revision 15 by early August. Files are fetchable at that URL pattern **before** the
archive page links them.
[HTS archive](https://www.usitc.gov/harmonized_tariff_information/hts/archive/list)

The `reststop` API serves only the current schedule; it **ignores** `release=` and
`revision=` parameters. The `hts.usitc.gov/download?release=` URL is a single-page-app shell
returning identical HTML regardless of parameters and is not a data endpoint.

**USITC DataWeb is the wrong tool for this project.** It requires a registered account plus
Login.gov multi-factor authentication, and it returns trade *statistics* — import and export
values by HTS code — rather than schedule and duty-rate data.
[DataWeb login process](https://www.usitc.gov/dataweb_login_process)

### The Chapter 99 stacking model — the most important modeling finding

Chapter 99 codes are **not products**. They are duty *modifiers* that stack on top of a base
Chapter 1–97 classification. Verified from live data:

```
9903.01.01  general = "The duty provided in the applicable subheading + 25%"
9903.01.05  general = "The duty provided in the applicable subheading + 10%"
            description = "Potash that is a product of Mexico..."
```

Chapter 99 subchapters by current record count:

| Subchapter | Records | Contents |
|---|---|---|
| 9902 | 1,655 | Miscellaneous Tariff Bill temporary duty suspensions |
| 9903 | 622 | **Section 301, Section 232, and IEEPA actions** |
| 9904 | 512 | Tariff-rate quota overage rates |
| 9908 | 5 | Quantitative-limit provisions |
| 9901 | 2 | Narrow legacy provisions |

**The consequence is load-bearing.** There is no first-party field stating "the current
Section 301 rate for HTS 8481.20 from China." Computing landed duty requires holding the
base HTS record, separately holding the active Chapter 99 provisions, and **matching each
provision's free-text scope description against product and country of origin**.

That is a text-matching problem, not a join. It is also precisely the argument the capstone
wants to make about platform capability, so it strengthens A1's thesis rather than
threatening it — but the domain model must not assume a clean structured join.

### Revision diffing — a working, optional enhancement

Consecutive revisions were fetched and diffed byte-for-byte to test whether annex content
could be recovered structurally instead of by OCR.

**What works.** For narrowly targeted, product-specific actions, ordinary Chapter 1–97 lines
carry a `footnotes` entry reading `"See 9903.XX.XX."` cross-referencing the applicable
Chapter 99 heading. **789 lines carry such a footnote in the current schedule**, and these
demonstrably change between revisions. For classic Section 301 product lists and Section 232
derivative lists, the affected-product list is fully machine-readable.

**A first-party changelog provides the join key.**
[Modifications to the HTS](https://www.usitc.gov/harmonized_tariff_information/modifications_to_hts)
lists 345 entries, each tagged with revision number, source type, legal authority
(Section 301, Section 232, and so on), country, **and a link to the originating Federal
Register document** in the same `document_number` format the FR API uses. This gives a
direct `HTS revision ↔ Federal Register document ↔ legal authority` join with no fuzzy
matching. It is HTML-only — no JSON:API backing was found — but it is 14 pages of ordinary
scraping.

**Verified example.** A single notice can span several revisions because of staggered
effective dates. The Brazil action (FR document 2026-14542) resolves as: revision 11→12 added
`9903.05.01`–`9903.05.09`; 12→13 added `9903.05.20`–`9903.05.99`; 13→14 added
`9903.04.60`–`9903.04.69` plus description edits inserting "patented pharmaceutical
articles", matching that notice's literal amendatory instruction.

**What does not work, and why.** That notice's Annex II has **no footprint in the revision
data at all** — zero attributable non-Chapter-99 changes. The reason is legal rather than
technical: "all products of country X except those listed" is a blanket country-of-origin
rule living in a Chapter 99 heading's prose U.S. Note, never as a per-line tag. **For broad
country-wide actions with exclusion annexes, structural diffing cannot substitute for OCR.**

## Q6 — anchor filer. **Resolved 2026-08-05: Mueller Water Products (MWA).**

Four candidates were evaluated by fetching the actual filings from EDGAR and extracting
quoted sentences. No quote below is reconstructed. **Mueller Water Products was selected**
(project decision, recorded below); the other three are retained as evaluated alternatives
in case the domain model runs into trouble.

The selection trades the simplest possible structure for the best test ground truth.
Gorman-Rupp's verbatim "single operating segment" would have been easier to model, but
Mueller's Item 1A and MD&A carry **quantified** tariff impact — percent-of-COGS figures and
per-segment margin attributions — which converts directly into unit-test assertions. Since
tests are explicitly named in the top-3 judging criteria, and the brief identifies free
labelled ground truth as the single most useful finding of the selection session,
quantified language is worth more than one fewer segment.

### 1. Gorman-Rupp Company (GRC) — simplest domain model

CIK 42682 · NYSE: GRC · approx. $2.1B market capitalisation · FY2025 10-K
([filing](https://www.sec.gov/Archives/edgar/data/42682/000119312526084820/grc-20251231.htm))

- Segment disclosure states **"the Company's single operating segment"** — the simplest
  structure of any candidate.
- Named inputs: "castings (for which most patterns are made and owned by the Company),
  structural steel, bar stock, motors, solenoids, engines, seals, and plastic and elastomeric
  components are purchased from other suppliers and manufacturers."
- Item 1A carries the risk-factor heading "U.S. trade policy, including the implementation of
  tariffs, could adversely affect the Company's business and financial results", and states
  "These tariffs... may increase the cost of imported materials used by our suppliers and in
  our products."
- Products map to **HTS 8413** (pumps for liquids); castings inputs to 7325 / 8483.
- Trade-off: tariff language is qualitative, with no dollar or percentage figures.

### 2. Mueller Water Products (MWA) — **SELECTED**

CIK 1350593 · NYSE: MWA · approx. $4.0B · FY2025 10-K, fiscal year ending 09-30
([filing](https://www.sec.gov/Archives/edgar/data/1350593/000135059325000066/mwa-20250930.htm))

- Two reportable segments (Water Flow Solutions, Water Management Solutions), both
  valve-adjacent.
- Named inputs: "brass ingot, scrap steel, sand and resin", and "scrap steel, sand, resin,
  brass ingot and steel pipe".
- Quantified tariff language, the richest of the four: "higher direct tariff costs of
  approximately 3% of costs of goods sold are expected to continue to contribute to
  inflationary pressures in 2026"; "While newly implemented tariffs are adversely impacting
  several product lines, Repair and Specialty Valve product lines are bearing most of the
  higher costs." MD&A repeats per-segment margin attributions across quarters.
- Products map to **HTS 8481** (valves) and 7325 (cast iron articles).

### 3. Hexcel Corporation (HXL) — best composites fit

CIK 717605 · NYSE: HXL · approx. $7.8B · FY2025 10-K
([filing](https://www.sec.gov/Archives/edgar/data/717605/000119312526046377/hxl-20251231.htm))

- Two segments; Composite Materials dominant.
- The most specific input list of any candidate: "epoxy and phenolic resins, acrylonitrile,
  carbon fiber, fiberglass yarn, aramid paper and, to a lesser extent, aluminum foil", plus
  "We manufacture high performance carbon fiber from polyacrylonitrile precursor ('PAN'). The
  primary raw material for PAN is acrylonitrile."
- Tariff language: "tariffs have increased the cost of materials used to manufacture our
  products"; "Lower margins for 2025 as compared to the prior year were due to sales mix,
  tariffs, and inventory reduction actions."
- HTS mapping spans several chapters (5501/5503, 6815, 3921/3926, 7019), which is more
  sprawling than the valve companies.

### 4. Watts Water Technologies (WTS)

CIK 795403 · NYSE: WTS · approx. $11.6B · FY2024 10-K
([filing](https://www.sec.gov/Archives/edgar/data/795403/000155837025001102/wts-20241231x10k.htm))

- Three **geographic** segments, so the product taxonomy is more unified than the count
  suggests.
- Named inputs: "bronze, brass, cast iron, stainless steel, steel, and plastic."
- Tariff language: "The new, substantial tariff increases on imports to the United States
  from Canada and Mexico (in addition to China)... could adversely impact the gross margin we
  earn on our products."
- Trade-offs: market capitalisation sits at the top of the mid-cap band, and a newer FY2025
  filing may now exist — check EDGAR before committing.

### Not viable: packaging machinery

No suitable public filer was found. The significant packaging-machinery pure-plays are
private-equity owned and file no 10-K. Hexcel adequately covers the third product shape
suggested in the brief.

## Q7, Q8 — B1 fallback: EDGAR and XBRL

### Verified access policy

- No API key or registration for `data.sec.gov`, `efts.sec.gov`, or `www.sec.gov/Archives`.
- Published limit: **10 requests per second**, with a declared User-Agent required.
- Bulk alternatives exist and are the correct ingest path: `companyfacts.zip` and
  `submissions.zip` under `/Archives/edgar/daily-index/`, rebuilt nightly, plus quarterly
  full-index files back to 1994Q3.
  [Accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
  [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

### Verified XBRL APIs

- `companyfacts`, `companyconcept`, `frames`, and `submissions` are officially documented and
  keyless. Frame period format: `CY####` annual duration, `CY####Q#` quarterly duration,
  `CY####Q#I` **instantaneous** (balance-sheet dates).
  [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- `company_tickers.json` is an **object keyed by string index**, not an array, and `cik_str`
  is an unpadded integer — pad to 10 digits for API URLs.
- Document URLs are built as
  `https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/{primaryDocument}`.
- **Full-text search** at `https://efts.sec.gov/LATEST/search-index` works and covers filings
  since 2001, but it is **not listed on SEC's official APIs page** — it is the search UI's
  backend, and SEC could change it without notice. It caps at 10,000 results
  (`from + size <= 10000`) and offers keyword/boolean matching only; "Natural language search
  capabilities are not currently supported."
  [EDGAR full-text search FAQ](https://www.sec.gov/edgar/search/efts-faq.html)

### Q8 — concept coverage, tested against six real mid-cap filers

Tested on MSA Safety (66570), Cabot (16040), Watts Water (795403), Integer Holdings
(1114483), Fabrinet (1408710), and Halozyme (1159036).

**Revenue-tag fragmentation is real and severe — a clean three-three split.** MSA, Cabot,
Fabrinet, and Halozyme report under `Revenues`. Watts and Integer report **only** under
`RevenueFromContractWithCustomerExcludingAssessedTax` and carry no `Revenues` fact at all.
A screener hardcoding either tag silently drops roughly half its universe; query both and
coalesce.

Same pattern, smaller scale: `Liabilities` is missing for Cabot and Watts;
`ResearchAndDevelopmentExpense` and `DepreciationDepletionAndAmortization` are missing for
Integer and Fabrinet — a legitimate consequence of contract-manufacturer reporting, not a
tagging error.

**Present in all six and safe to screen on:** `NetIncomeLoss`, `OperatingIncomeLoss`,
`Assets`, `StockholdersEquity`, `CashAndCashEquivalentsAtCarryingValue`,
`LongTermDebtNoncurrent`, `EarningsPerShareDiluted`, `GrossProfit`.

The `srt` taxonomy was **absent entirely** from all six; only `dei` and `us-gaap` appeared.
Do not plan around it.

### Q7 — Item 1A / Item 7 extraction is the real risk

- Filings are inline XBRL, but **iXBRL tags numeric and dei facts, not sections**. Nothing
  marks a region as Item 1A.
- Table-of-contents anchors are **opaque generated hashes** (for example
  `#i071949740f904116badf322ece477e91_19`), not semantic IDs, and differ per filing.
- **The false-positive rate was measured, not estimated.** In one real 10-K, the literal
  string "Item 1A" appeared 3 times and **only 1 was the section heading**; the others were
  cross-references, including one inside Item 1A's own body. For Item 7, 1 of 2.
- Recommended approach: match heading-formatted occurrences specifically rather than any
  occurrence; reject matches inside cross-reference sentences; validate that extracted
  sections exceed a plausible length threshold.
- Failure modes: filings that omit Item 1A or Item 1B, 10-K/A amendments that contain only
  some items, and filers splitting MD&A across Items 7 and 7A.
- **No first-party SEC product pre-extracts narrative sections.** The Financial Statement
  Data Sets are numeric face-financials only.
  [Financial Statement Data Sets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets)

**The dangerous property is the failure mode.** A mis-sliced section does not raise an error
— it silently corrupts the embedding corpus. "It parsed without an exception" does not mean
"it parsed correctly", so B1 requires an explicit extraction-validation step.

### Consequence for the brief's risk ranking

`../capstone-brief.md` calls B1 the "lowest data risk of the set". That is true of the
financial data and false of the corpus. Federal Register text is born-digital and
machine-delimited; 10-K narrative sections are neither. B1's structured half is safer than
A1's; its unstructured half — the half that satisfies capstone component 3 — is
considerably riskier.

## Q9 — A2 / GDELT: rejected

- The **DOC 2.0 API returns no article body**. Response fields are `url`, `url_mobile`,
  `title`, `seendate`, `socialimage`, `domain`, `language`, and `sourcecountry`. GDELT's own
  launch post confirms metadata only.
  [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- It is keyless but **actively rate-limited** — every live call attempted in this pass
  returned HTTP 429. No numeric limit is published.
  [API quotas](https://blog.gdeltproject.org/behind-the-scenes-api-quotas-the-impact-of-a-fraction-of-a-qps/)
- Default search window is a rolling 3 months, extendable to a year; history begins 2017.
  [Full-year searching](https://blog.gdeltproject.org/doc-geo-2-0-api-updates-full-year-searching-and-more/)
- Reaching actual article text means dropping to GKG 2.0 CSV files or the BigQuery public
  dataset — semicolon and pipe-delimited parsing, and in the BigQuery case a **second cloud
  credential** outside the Databricks environment.
  [GDELT data](https://www.gdeltproject.org/data.html)
- **Supplier-name matching has no GDELT-provided solution.** `V2Organizations` is raw NLP
  extraction explicitly tuned to err on the side of inclusion — recall over precision — with
  no disambiguation, no subsidiary linkage, and no ticker resolution. The Global Entity Graph
  is a static 2019 baseline and does not help.
  [Global Entity Graph](https://blog.gdeltproject.org/announcing-the-global-entity-graphs-geg-g1-baseline-dataset-8-billion-entities-from-2019/)

**Conclusion.** A2's premise in the brief — that it shares the relational spine and only the
corpus differs — is true but misleading, because the corpus is the expensive part. Matching
news mentions to a suppliers table requires a hand-built fuzzy entity-resolution layer with
empirically tuned thresholds. That is a multi-day project, not a spare-time extension. A2
should move to the brief's rejected-ideas table. It remains usable as a "what we would build
next" slide, provided the data limitation is stated honestly.

## Backup corpora for A1

### CBP CROSS — strongest backup, but found rather than provided

The Customs Rulings Online Search System has **no documented API and no bulk download**; its
data.gov entry links back to the search UI and was last updated in 2022.
[CROSS on data.gov](https://catalog.data.gov/dataset/cbp-customs-rulings-online-search-system-cross)

However, the site's frontend is served by a working, keyless JSON backend:

- `https://rulings.cbp.gov/api/search?term=<q>&pageSize=<n>&page=<n>` returns
  `{rulings[], totalHits}`. Each entry carries a structured **`tariffs`** array of HTS
  strings, plus `rulingNumber`, `subject`, `categories`, `rulingDate`, and `collection`.
- `https://rulings.cbp.gov/api/ruling/{rulingNumber}` adds a `text` field with the complete
  ruling letter.

The corpus is large and well-shaped for retrieval: `totalHits` for "tariff" is **200,836**,
spanning roughly 1989 to the present. Ruling 955022 runs about 760 words in a
**FACTS → ISSUE → LAW AND ANALYSIS → HOLDING** structure containing real General Rules of
Interpretation and chapter-note reasoning — substantive classification argument, not
one-line determinations. Uniquely among the sources examined, its HTS codes are a
**structured field** rather than something to extract from prose.

**Treat this as found, not provided.** There is no developer documentation, no published
rate limit, and no terms-of-use commitment. It is the frontend's private backend, reachable
because nothing blocks it, not because CBP sanctions programmatic use. It may change or
block without recourse. Keep any ingest low-volume and polite, and do not place the critical
path on it. Filter to `categories: "Classification"` — a Section 337 advice ruling returned
an empty `tariffs` array.

### Assessed and not recommended

- **govinfo.gov** is redundant. Its Federal Register XML is the same underlying GPO bulk XML
  the Federal Register API already serves, gated behind a free `api.data.gov` key. It is a
  fallback access path, not a quality upgrade. [govinfo API](https://api.govinfo.gov)
- **USITC as a text corpus** is a dead end. EDIS covers Section 337 investigation metadata
  with no HTS field, and AD/CVD orders publish as a spreadsheet. Whatever prose exists
  appears in Federal Register notices anyway. USITC remains essential for schedule data.
- **Census Schedule B** applies to exports and uses different final digits from HTS. It is
  not substitutable for import classification and is not needed unless an export-compliance
  angle is added later.

## Project decisions

Implementation choices, not verified facts:

- **Proceed with A1.** The existential dependency is resolved.
- **Scope A1 to scope-description matching, not exhaustive annex line-item coverage.** This
  is the honest product given image-only annexes, and it is also the stronger demo, because
  scope descriptions are prose — which is what justifies semantic retrieval over SQL. State
  the annex limitation openly rather than under-covering it silently.
- **Base the initial build on the current Chapter 99 snapshot.** The 622 active records
  answer the headline question — which components are hit by an active trade action, and at
  what rate — as a static join on country of origin plus HTS code. Revision diffing is a
  well-understood enhancement worth roughly half a day, not a dependency.
- **Anchor on Mueller Water Products (MWA), CIK 1350593** — decided 2026-08-05. Chosen over
  Gorman-Rupp's simpler single-segment structure because its quantified tariff language
  yields stronger test assertions. Two consequences the domain model must absorb:
  - **Two reportable segments** (Water Flow Solutions, Water Management Solutions), so the
    product hierarchy needs a segment level rather than a flat product list. Both are
    valve-adjacent, so the taxonomy stays coherent.
  - **Fiscal year ends 09-30**, not 12-31. Any period alignment against calendar-quarter
    data — including SEC XBRL `frames`, whose periods are calendar-based — must not assume
    a December year end.
  - Primary HTS targets: **8481** (valves) and **7325** (cast iron articles) for
    hydrant and fitting castings. Named inputs to model as components: brass ingot, scrap
    steel, sand, resin, steel pipe.
  - The FY2025 10-K's quantified statements are the **test ground truth** — in particular
    "higher direct tariff costs of approximately 3% of costs of goods sold" and the
    Repair/Specialty Valve concentration. Write exposure-logic assertions against these
    before building scoring, per the brief's tests-as-deliverable decision.
- **Treat CBP CROSS as a documented backup**, not a planned integration.
- **Retain B1 as the fallback**, with the corrected understanding that its narrative
  extraction — not its financial data — is the risk to budget for.

## Local observations

Not claims about the sources themselves:

- `WebFetch` was observed returning a plausible but partly fabricated summary of a Federal
  Register page during this research. Findings were re-derived with direct HTTP requests.
  For verification work against these APIs, prefer raw fetches and inspect the response.
- `www.usitc.gov` static-file paths returned 403 to some clients while
  `hts.usitc.gov/reststop` did not, which is consistent with per-host bot mitigation rather
  than a per-project block.

## First-party references

- [Federal Register API documentation](https://www.federalregister.gov/developers/documentation/api/v1)
- [Federal Register document 2026-15975](https://www.federalregister.gov/documents/2026/08/05/2026-15975)
- [Federal Register document 2026-15220](https://www.federalregister.gov/documents/2026/07/28/2026-15220)
- [Federal Register document 2026-14542](https://www.federalregister.gov/documents/2026/07/20/2026-14542)
- [USITC HTS](https://hts.usitc.gov/)
- [USITC HTS archive](https://www.usitc.gov/harmonized_tariff_information/hts/archive/list)
- [Modifications to the HTS](https://www.usitc.gov/harmonized_tariff_information/modifications_to_hts)
- [USITC DataWeb login process](https://www.usitc.gov/dataweb_login_process)
- [SEC: Accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC EDGAR full-text search FAQ](https://www.sec.gov/edgar/search/efts-faq.html)
- [SEC Financial Statement Data Sets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets)
- [CBP rulings (CROSS)](https://rulings.cbp.gov/)
- [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [GDELT data](https://www.gdeltproject.org/data.html)
