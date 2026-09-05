# AI-Powered Prospectus Analysis and Review System

**Senior project · thirteen phases · full stack · for the Capital Market
Authority (CMA)**

## The problem

A prospectus is the document a company must publish before offering securities
to the public. They are long (the sample here is 195 pages), dense, and legally
significant. CMA reviewers must check that required disclosures are present,
that figures are consistent, and that risks are properly stated. It is slow,
repetitive work where a missed inconsistency matters.

## What the system does

An LLM-powered web platform for CMA employees. The core idea: **do not ask an
AI to swallow a 195-page document on every question.** Extract, organise, index
and structure the document *once*, then let reviewers interrogate that
structure in natural language.

**Understand** — (1) executive summaries of large prospectuses; (2) answer any
reviewer question in natural language.
**Extract** — (3) financial indicators: revenue, profit, debt, assets,
liabilities, cash flow and others; (4) risk factors, categorised and
summarised.
**Verify** — (5) are required sections and disclosures present; (6) do figures
or statements conflict across sections; (7) how did indicators move across
years, and which movements are significant.
**Compare** — (8) companies in the same sector; (9) a revised prospectus
against an earlier submitted version.
**Report** — (10) a preliminary report of findings, missing information,
unusual figures, and areas needing human review.

Cutting across all ten: **the page and section supporting every important
AI-generated answer.**

## Priority: the core must be excellent before the edges are broad

All ten requirements ship — the list is fixed. But they are **not equally
important**, and effort is allocated accordingly.

**Tier 1 — the project is judged on these.** Executive summaries (1),
question answering (2), and citations (5). The bar is *correct answers that
are not stupid, with sources*. Quality here beats every other feature.

**Tier 2 — substantial features, normal quality bar.** Financial indicator
extraction (3), risk factors (4), missing sections (7), conflicting figures
(8), year-over-year changes (6), the preliminary report (10).

**Tier 3 — the last thing built.** Comparison (9). Of the two modes,
**cross-company sector comparison matters more** than same-company-across-time,
so it is built first. Both come after everything else works.

Two consequences that change the plan:

- **Retrieval quality is the whole ballgame.** A wrong or vague answer is worse
  than useless for a regulator, and it costs reviewer time rather than saving
  it. Phases 3, 4 and 5 — retrieval and answering — carry the most weight of
  any phases in the project.
- **Evaluation starts in Phase 3, not at the end.** "Answers that are not
  stupid" cannot be improved unless it is measured. The golden question set is
  written in Phase 3 and re-run after every change to chunking, retrieval or
  prompts. Phase 13 then becomes final measurement and write-up rather than
  first measurement.

### Answer behaviour — decided

**Executive summary is layered.** A ~300-word overview first, with any part
expandable into detail on request. The reviewer controls the depth. A four-page
summary of a 195-page document has not saved anyone much time.

**Partial answers are given, with the gap named.** When the prospectus only
partly answers a question, the assistant states the supported part with its
citation and then says explicitly what the document does not state. It does not
refuse outright — over-refusing wastes reviewer time as surely as a wrong
answer — and it never fills the gap with an invented figure. "Not found in the
document" remains correct when nothing supports an answer at all.

### The golden question set

There are no CMA reviewers available: the users during development are the
student and the examining professors. The question set is therefore
**self-authored**, and should be written as *the questions an examiner would
ask in the defence*, plus deliberately hard ones. Roughly 40 questions, each
recorded with its expected answer, expected page(s) and section, in four
categories:

1. **Factual lookup** — stated plainly on one page.
2. **Figure lookup** — a specific number, unit and year.
3. **Synthesis** — requires combining two or more places in the document.
4. **Absent information** — the document genuinely does not say. The correct
   behaviour is refusal, and these catch invention, which is the single most
   dangerous failure mode.

Built in Phase 3 alongside retrieval, re-run after every change to chunking,
retrieval or prompts. Its purpose is regression detection, not a final grade:
it tells you whether a change made the system better or worse, which is
otherwise impossible to know.

### Document scope: three markets, three rulebooks

The CMA runs three offering regimes and **each has its own required
disclosures**. A prospectus is filed under exactly one of them, and the market
decides which checklist and which indicators apply:

| Market | What it is | Disclosure burden |
|---|---|---|
| **sukuk** | Islamic bonds — debt, not shares | programme terms, Shari'ah approval, profit distribution, Sukukholder rights |
| **tasi** | the Main Market, largest companies | heaviest — full financial, governance and ownership disclosure |
| **nomu** | the Parallel Market, smaller companies | lighter than TASI, and qualified-investor restrictions |

Nothing may hard-code one market. The market is taken from the folder a PDF
sits in (`sukuk/`, `tasi/`, `nomu/`) rather than guessed from the text: whoever
files the document already knows which market it belongs to, so inferring it
would add a chance of being wrong for no benefit.

**The library**

| Market | Document | Pages |
|---|---|---|
| sukuk | Riyad Bank Sukuk Offering Prospectus | 195 |
| tasi | Naseej International Trading Company — Rights Issue | 258 |
| nomu | Jamjoom Fashion Trading Company | 408 |

Three markets, three companies, three documents — enough to build and
demonstrate everything except same-company-across-time comparison.

**All three checklists** come from the official CMA disclosure requirements,
which are published on the CMA website and which the user can read. Requirement 7 must be built against those real lists, not
a list inferred from a sample document's own contents page — an inferred
checklist can only ever find sections the document already has, which makes the
feature circular. Needed by Phase 10; earlier is better, since they also tell
us what the Phase 8 summary should highlight.

### Report format and materiality — decided

**The preliminary report (requirement 10) is a well-formatted answer in the
chat.** No PDF or Word export is required. This keeps everything inside the
conversation, consistent with the product being an assistant rather than a
document generator.

**"Significant change" (requirement 6) is judged by the LLM**, case by case,
rather than by a fixed percentage threshold. A 3% move in capital adequacy can
matter more than a 30% move in a small balance-sheet line, and only judgement
in context can tell them apart. Code still computes the differences exactly;
the LLM decides which ones are worth a reviewer's attention.

## The product: a chat assistant, not a dashboard

**The objective is to reduce CMA reviewer time.** Every design decision is
judged against that. A tool with six screens to learn does not save anyone
time.

So the final product has the shape of Claude or ChatGPT — a conversation with
an assistant that knows the prospectus — not a web app with a navigation bar:

- The reviewer **asks in plain English and gets a real answer in plain
  English.** The citation is an annotation *on* the answer, not a substitute
  for it. "Not found in the document" is still a valid answer; "here is page
  88, go read it" is not.
- **It speaks first.** As soon as a document finishes ingesting, the assistant
  opens with a briefing: findings, missing information, unusual figures,
  conflicts, and areas requiring human review. The reviewer should not have to
  know what to ask in order to be warned.
- **Modes, not screens.** Comparison is a mode within the same interface — the
  way Claude places Chat, Cowork and Code beside one another — not a separate
  window the reviewer navigates to. The conversation is continuous across
  modes.
- **The PDF sits beside the chat.** Clicking a citation opens the source page
  in a pane next to the conversation, so verification never costs a context
  switch.

**Comparison has two equally required modes**, both answered inside the
conversation rather than on a separate screen:

1. **Same company, different time periods** — this year's submission against
   last year's. What changed, what was removed, which figures moved.
2. **Different companies, same sector** — this bank's sukuk prospectus against
   another Saudi bank's.

**Reviewers have individual accounts and their conversations are saved**, so a
review can be picked up where it was left. The uploaded prospectuses form a
**library**: any conversation can pull in one document or several, which is
also what makes comparison work without a special second window.

### "Learning" the prospectus means indexing, not training

The assistant is **not fine-tuned** on prospectus data. Fine-tuning dissolves
text into model weights, and weights have no page numbers — which makes it
fundamentally incompatible with Rule 1. Instead the document is read, indexed
and retrieved from, so every sentence the assistant produces stays traceable to
a page a reviewer can open. The reviewer's experience is an assistant that
knows the document; the mechanism is retrieval.

---

## Standing rules

Not negotiable. They apply to every phase.

### Rule 1 — Every answer must cite its source page and section

Any output shown to a reviewer — an answer, a figure, a risk, a flagged
conflict, a line in the report — must carry a citation: **page number** and
**section**. No citation means the output is not shippable.

This governs design, not just output. If a feature cannot produce a citation,
we redesign the feature rather than dropping the citation. Concretely: document
id, page and section are attached to every chunk at the moment of extraction
and travel with it all the way to the reviewer's screen.

Corollary: **never invent a figure.** No number appears in output unless it was
literally read out of the document. If the retrieved text does not contain the
answer, the correct output is **"Not found in the document"**. For a regulator,
a confident wrong number is worse than no number.

### Rule 2 — Explain things simply to the user

The user is **new to coding and is learning while building this**. So:

- Explain *why* before *how*.
- Plain language first; define a technical term the first time it appears.
- Small working steps over large clever ones.
- Say what to expect *before* running a command; explain the output after.
- Comment code more heavily than a normal project would.
- **Lead the learning.** When an upcoming step needs a concept the user has not
  met, name it and say "go learn this" — do not wait to be asked. Every month
  carries an explicit *Learn* list.
- Report honestly when something works badly. A weak result that is explained
  teaches more than a good result that is not.

### Rule 3 — Ambitious by design

This is a senior project and the system is meant to be genuinely LLM-native and
full stack, not a keyword tool with a chat box bolted on. Individual *steps*
stay small and understandable; the *architecture* does not get scaled down to
match current skill level.

Where a deliberately simple technique is used as a stepping stone, it is
labelled as one, and the month that replaces it is named. Nothing impressive
gets deferred to a vague "later" where it risks never being built.

---

## Architecture

### The full-stack picture

```
  BROWSER — a chat, not a dashboard
  React + Tailwind
  one conversation · modes: Ask / Review / Compare · PDF pane beside the chat
  proactive opening briefing when a document finishes ingesting
        |  HTTP / JSON  (streaming for answers)
        v
  BACKEND                                     FastAPI (Python)
  auth · upload · jobs · search · ask · extract · checks · report
        |                         |                        |
        v                         v                        v
  PostgreSQL                 Vector index            Claude API
  documents, chunks,         chunk embeddings        claude-opus-5
  figures, risks,            (pgvector)              answers, extraction,
  findings, users                                    agent, judging
        ^
        |
  WORKER  background ingestion jobs
  (a 195-page PDF takes minutes — it cannot run inside a web request)
```

### The document pipeline

```
  PDF
   |
   v
 [1] INGEST          text per page  +  page images (for tables and charts)
   |
   v
 [2] STRUCTURE       LLM-assisted outline: headings, sections, hierarchy
   |                 -> every chunk tagged (document, page, section)
   v
 [3] INDEX           embeddings (meaning) + keyword index (exact terms)
   |
   v
 [4] RETRIEVE        query decomposition -> hybrid search -> LLM reranking
   |
   +----------------+-------------------+---------------------+
   |                |                   |                     |
   v                v                   v                     v
 [5] ANSWER     [6] SUMMARISE      [7] EXTRACT           [8] AGENT
  cited,          map-reduce         financials + risks    tool-using,
  grounded,       section ->         -> structured         multi-step
  refuses when    document           TABLES                investigations
  unsupported                          |
                                       v
                                 [9] VERIFY
                                  LLM finds candidates
                                  code verifies arithmetic
                                  LLM judges materiality
                                       |
                                       v
                                 [10] REPORT
```

### Where the intelligence lives

**Retrieval is semantic, not lexical.** Chunks are embedded as vectors so the
system matches *meaning*: a reviewer asking about "main business" finds "the
Bank is a licensed Saudi joint stock company providing retail and corporate
banking services" even though not one keyword matches. Keyword search is kept
alongside it — prospectuses are full of exact terms (defined terms, SAR
figures, section names) where literal matching genuinely wins. Running both and
fusing the results is **hybrid search**, and it beats either alone. The keyword
half is a *component*, never the architecture.

**The agent is the ambitious core.** Rather than a single retrieve-then-answer
shot, Claude is given tools — `search_document`, `get_page`, `lookup_figure`,
`list_sections`, `compare_documents` — and plans its own multi-step
investigation. "Are the revenue figures consistent?" becomes: find every
revenue mention, extract each with its page, compare them, judge whether
differences are real conflicts or restatements, report with citations.

### The one thing that stays deterministic

**The LLM reads and judges. Code does the arithmetic.**

| Step | Who | Why |
|---|---|---|
| Find every mention of revenue in 195 pages | **LLM** | Must know "total operating income" counts |
| Pull number, year, unit, page out of each | **LLM** | Reading prose and tables |
| Determine 1,240 != 1,420 | **Code** | Must be exact and identical on every run |
| Judge whether that gap is material | **LLM** | Needs judgement and context |

Only the arithmetic is fixed, because a regulator's findings must be
reproducible and defensible line by line. Intelligence sits on both sides of it.

### Multi-document from day one

Requirements 8 and 9 mean a **library** of documents. Every chunk, figure and
risk carries a `document_id` from the start. Retrofitting that later means
rewriting everything.

---

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.13.1 | installed |
| Backend | FastAPI | async, automatic API docs |
| Database | PostgreSQL + **pgvector** | one database for both rows and vectors |
| Background jobs | Celery or FastAPI background tasks + Redis | ingestion takes minutes |
| Frontend | React + Vite + Tailwind | **needs Node.js — not yet installed** |
| PDF viewer | PDF.js in the browser | so citations can jump to the page |
| LLM | Claude API, `claude-opus-5`, `anthropic` Python SDK | |
| Embeddings | dedicated embedding model — chosen in Phase 2 | English-only; local open model vs. hosted |
| Auth | JWT sessions, reviewer/admin roles | |
| Packaging | Docker + docker-compose | for the final deployment |
| Testing | pytest | |
| Version control | git + GitHub | installed |

**Why Claude:** the Claude API has a built-in **citations** feature for PDFs
that returns the actual page numbers each sentence was drawn from — the
citation comes from the API itself rather than from asking the model nicely. It
also reads **page images**, which matters because financial statements are
tables and tables extract badly as text. Both are direct matches for Rule 1.

**API key:** in a `.env` file, git-ignored. Never hardcoded, never committed.

---

## Open questions and dependencies

**Document type — CONFIRMED.** The page header reads *"Riyad Bank Sukuk
Offering Prospectus"*. This is a **sukuk (Islamic bond) offering prospectus for
a Saudi bank**, not an equity IPO. Consequences: the required-disclosures
checklist in Phase 7 must be the sukuk/debt one, not the equity one (no offer
price, no share count; instead issuance programme terms, Shari'ah approval,
profit distribution mechanics); and the Phase 6 indicators are bank indicators
(net financing income, capital adequacy, non-performing loans) rather than
generic corporate ones. **Resolved:** the delivered system must handle **both** sukuk
and equity IPO prospectuses, so the offering type is detected at ingestion and
drives which checklist and indicator set is used.

**Page numbering offset — critical for Rule 1. SOLVED in Phase 2.** The number
printed on a page does not match the PDF's own page count, because of
unnumbered front matter — and the gap differs per document: **sukuk 22, tasi
41, nomu 43**. A citation showing the PDF index would send a reviewer dozens of
pages from the answer, with nothing erroring and nothing looking wrong.

`src/pagemap.py` works the offset out per document from evidence rather than
hard-coding it, and refuses to guess when the evidence is weak. Verified
independently: 99% (sukuk), 93% (tasi), 97% (nomu) of numbered pages show the
number the offset predicts. Every chunk carries **both** `pdf_page` and
`printed_page`; front matter has no printed number, so `printed_page` is null
and the citation says "PDF page 4" rather than inventing one.

**More documents needed — now a hard blocker, not a nice-to-have.** Both
comparison modes are must-ship, so the demo needs a minimum of three documents
and ideally four:

| # | Document | Enables |
|---|---|---|
| 1 | Riyad Bank Sukuk Offering Prospectus | have it |
| 2 | Another Riyad Bank prospectus from a different period | same-company-over-time comparison |
| 3 | Another Saudi bank's sukuk prospectus | cross-company sector comparison |
| 4 | **An equity IPO prospectus** | now required — the system must handle equity, and it cannot be tested on a document type we do not have |

Without #2 and #3 two must-ship requirements cannot be demonstrated at all.
Collect these during Phases 1-3. This is the single most likely way the project
loses features.

**Node.js is not installed.** Needed from Phase 5. Install it in Phase 4.

---

## Build plan

Thirteen phases in six stages. **The calendar does not matter; the sequence
does.** A phase ends when it is runnable, demonstrable and understood — not
when a month is up.

### Priority is not the same as sequence

The chat interface is one of the highest-priority parts of this project, and it
is still not built first. Priority decides *where quality effort goes*;
dependency decides *what order things are built in*. A chat window with nothing
behind it is a demo of a text box. The order below reaches a working product as
early as dependencies allow, then deepens it.

---

### Stage A — The document becomes machine-readable

**Phase 1 — Foundations and ingestion.** DONE. Repo, venv, `.env`,
`.gitignore`, `src/config.py`, `src/ingest.py` (text per page + page image
rendering), extraction health check.

**Phase 2 — Structure.** Detect headings, build the document outline, tag every
chunk with its section, and carry **both** `pdf_page` and `printed_page` (the
sample document runs 22 apart). Detect the offering type (sukuk vs equity)
while we are here. This completes the citation.
*Learn:* regular expressions · chunking strategies and why chunk size changes
answer quality · what document structure means to a retrieval system.

### Stage B — Retrieval that is not stupid  *(Tier 1 foundation)*

**Phase 3 — Embeddings and the golden question set.** Convert chunks to vectors
and search by meaning. Write the ~40-question test set at the same time, and
take the **first measurement** — this is the baseline every later change is
compared against.
*Learn:* **embeddings** — text as vectors where closeness means similar meaning
· cosine similarity · vector indexes · how to score retrieval quality.

**Phase 4 — Hybrid search and reranking.** Fuse semantic and keyword results,
let the LLM rewrite and split hard questions, retrieve wide then rerank down.
Re-run the test set and show the improvement as a number.
*Learn:* hybrid search and rank fusion · **reranking** · query decomposition.

### Stage C — It answers  *(Tier 1)*

**Phase 5 — Grounded, cited answers.** Claude answers only from retrieved
chunks, cites page and section, gives partial answers with the gap named, and
refuses rather than inventing. Command line only.
*Learn:* the Claude API and Python SDK · system prompts · **grounding vs.
hallucination** · streaming · prompt caching · cost tracking.

### Stage D — It becomes a product

**Phase 6 — Backend and database.** PostgreSQL (documents, chunks, figures,
risks, findings, users, conversations, messages), FastAPI, background ingestion
worker with job status. Install Node.js this phase.
*Learn:* HTTP and REST · FastAPI · SQL and schema design · SQLAlchemy ·
Pydantic · background jobs.

**Phase 7 — The chat web app.** The message thread with streaming answers,
upload with progress, **citation chips that open the PDF beside the
conversation**, conversation history.
*Learn:* HTML/CSS/JS · React (components, props, state, effects) · calling an
API from the browser · Tailwind · PDF.js.
**End-to-end demo: upload, ask, get a cited answer, click through to the page.**
Everything after this phase is visible in the product immediately.

### Stage E — It gets intelligent

**Phase 8 — Summaries.** Layered executive summary: ~300 words, expandable per
section, every claim cited.
*Learn:* **map-reduce summarising** — summarise the parts, then the summaries.

**Phase 9 — Structured extraction.** Financial indicators and risk factors into
database tables with page and section. Vision on statement pages, because
tables extract badly as text. Indicator set chosen by offering type.
*Learn:* structured outputs and JSON schemas · vision/multimodal prompting ·
normalising financial numbers.

**Phase 10 — The checks and the agent.** Missing sections against the real CMA
checklist; conflicting figures; year-over-year movements with the LLM judging
materiality. Claude gets tools and plans multi-step investigations.
*Learn:* **tool use / function calling** · the agent loop · pytest ·
deterministic checks.

**Phase 11 — The proactive briefing and the report.** The assistant speaks
first when ingestion finishes, and the preliminary report as a formatted chat
answer assembled from parallel specialist passes.
*Learn:* orchestrating several LLM calls · separating findings from
presentation.

### Stage F — The last things

**Phase 12 — Comparison.** **Cross-company sector comparison first** (the more
valuable of the two), then same-company across time periods. Answered inside
the conversation, not on a separate screen.
*Learn:* diffing structured data · retrieval scoped to several documents.

**Phase 13 — Evaluation, hosting and defence.** Final measurement with
LLM-as-judge, bug fixing and polish, deploy online, final report, demo video,
defence.
*Learn:* LLM-as-judge · retrieval and citation metrics · Docker Compose ·
deployment · technical writing.

---

## Scope control

**Must ship** (the project fails without these): ingestion · semantic retrieval
· cited Q&A in a chat interface · the proactive opening briefing · financial
extraction · risk extraction · missing-section and conflict checks ·
comparison of the same company across time periods · reviewer accounts with
saved conversation history · the preliminary report as a formatted chat answer
· online deployment · the evaluation.

**Cut first if behind schedule**, in this order: admin role as distinct from
reviewer · **cross-company sector comparison** · the agent (fall back to fixed
pipelines for the checks).

Note the change of position on sector comparison. It was originally called
equally required, but the user then stated that comparison matters far less
than summarisation and answer quality. Both modes are still built; if something
has to give, the sector mode goes before anything in Tier 1 or 2 is weakened.

**Not cuttable, despite being late in the plan:** **online deployment**. The
project is full stack and must run online, not only on the student's laptop.
Plan the deployment target early rather than discovering hosting problems in
the final phase.

**Explicitly out of scope:** Arabic support. English only. If the project
finishes early it may be added, but nothing is designed around it. Switching to
a multilingual embedding model later costs one re-indexing run — minutes and
cents for a handful of documents — so deferring this is cheap.

**Never cut:** citations. They are the project's thesis.

**Buffer:** Phase 9 is evaluation and writing only. Do not plan features into
it. Every senior project overruns, and this phase is what absorbs it.

---

## Working agreements

**Working conditions.** The user commits **20+ hours a week** — this is their
main focus, not a side project. That budget is what makes the ambitious version
realistic rather than aspirational, so do the hard parts properly instead of
reaching for shortcuts. There are **regular supervisor meetings** rather than
one midterm demo, so every phase must end in something that can be shown and
explained, and sub-steps within long phases should be demoable too. **No
throwaway UI** — the real React app is built once, in Phase 7.

- **One step at a time.** Finish it, run it, understand it, then move on.
- **Every phase ends with a runnable demo.**
- **Explain the failure, not just the fix.** Reading an error message is the
  most transferable skill here.
- **Test against the real document.** `prospectus.pdf` decides whether
  something works.
- Ask before installing anything, and say what it does and why.
- Watch API cost. Embedding once is cheap; agent loops and whole-document
  passes are not. Use prompt caching and cache results to disk.
- **Keep a weekly logbook** — what was built, what broke, screenshots. The
  final report is far easier to write from notes than from memory.

---

## Current status

**Phases 1 and 2 complete**, committed and pushed to GitHub.

The library holds three prospectuses across three markets, ingested into
**3,413 citable chunks**, every chunk carrying document, market, section path,
`pdf_page` and `printed_page`:

| Market | Document | Pages | Chunks | Page offset (agreement / independently verified) |
|---|---|---|---|---|
| sukuk | Riyad Bank Sukuk Offering | 195 | 889 | 22 (88% / **99%**) |
| tasi | Naseej International Rights Issue | 258 | 1,219 | 41 (78% / **93%**) |
| nomu | Jamjoom Fashion Trading | 408 | 1,305 | 43 (87% / **97%**) |

All three documents turned out to have a usable **PDF outline** once authoring
junk was filtered out (`_Hlk...` Word bookmarks, and 165 exhibit/table captions
in the nomu file). The font-analysis fallback in `sections.py` is written and
tested but was not needed for these three — it exists because the next document
may not be so lucky.

**Modules:** `config.py` (paths, markets) · `documents.py` (library discovery,
market from folder) · `ingest.py` (orchestration, text, page images) ·
`pagemap.py` (printed-page detection) · `sections.py` (outline) ·
`boilerplate.py` (running-header removal) · `chunks.py` (chunking with
citations).

**Known gaps carried forward:**

- **13 pages have no text layer** (2 in tasi, 11 in nomu) and will need OCR.
  The sukuk document has none.
- Front-matter chunks have no printed page number; they correctly report
  "PDF page N" rather than inventing one.
- Boilerplate removal stripped 1.1% / 3.5% / 5.8% of raw text as running
  headers and footers. Worth re-checking in Phase 3 that nothing real was lost.
- `search_prospectus.py` is the throwaway keyword prototype written before
  setup. It is scaffolding and gets absorbed into the hybrid retriever in
  Phase 4.

**Next: Phase 3 — embeddings and the golden question set.**
