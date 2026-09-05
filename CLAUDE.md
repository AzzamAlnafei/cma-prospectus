# AI-Powered Prospectus Analysis and Review System

**Senior project · 9 months · full stack · for the Capital Market Authority (CMA)**

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
  BROWSER
  React + Tailwind
  library · upload · dashboard · ask · financials · risks · compare · report
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
| Embeddings | dedicated embedding model — chosen in Month 2 | local open model vs. hosted |
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
checklist in Month 7 must be the sukuk/debt one, not the equity one (no offer
price, no share count; instead issuance programme terms, Shari'ah approval,
profit distribution mechanics); and the Month 6 indicators are bank indicators
(net financing income, capital adequacy, non-performing loans) rather than
generic corporate ones. Still to confirm with the user: whether the delivered
system should target sukuk documents specifically, or be general enough for
equity IPOs too.

**Page numbering offset — critical for Rule 1.** The number printed on the page
runs **22 behind** the PDF page index: PDF page 136 is printed page 114. The
offset is consistent across the body of the document (verified at PDF pages 50,
100, 136, 151, 181) and comes from unnumbered front matter. A citation showing
the PDF index would send a reviewer to the wrong page of their copy. Every
chunk must therefore carry **both** numbers — `pdf_page` for internal lookups
and rendering, `printed_page` for anything shown to a reviewer. Front matter
before the numbering starts has no printed number and must be handled
explicitly rather than by blindly subtracting 22.

**More documents needed.** Requirements 7, 8 and 9 need multi-year figures, two
prospectuses in the same sector, and two versions of the same prospectus.
Collect these during Months 1-3, well before Month 8.

**Node.js is not installed.** Needed from Month 5. Install it in Month 4.

---

## Nine-month plan

Assumed timeline September - May; shift the calendar labels to match the real
academic schedule. Each month ends in something **runnable and demonstrable**.

### Month 1 — Foundations and ingestion
*Learn:* Python essentials (functions, dicts, comprehensions, files, error
handling) · virtual environments · git and GitHub · environment variables ·
JSON · how PDFs store text (no paragraphs, only positioned characters) · the
command line.
*Build:* repo and project structure · venv · `.env` · PDF text extraction per
page · page image rendering · first-pass section/heading detection · CLI.
*Deliverable:* the whole prospectus as structured JSON, every piece of text
carrying document, page and section. Pushed to GitHub.
*Academic:* project proposal / SRS document.

### Month 2 — Semantic retrieval
*Learn:* **embeddings** (text as vectors where closeness means similar meaning)
· cosine similarity · vector databases · chunking strategies · BM25 · hybrid
search and rank fusion · reranking.
*Build:* chunking with metadata · embedding pipeline · vector index · hybrid
retriever · LLM reranker · a retrieval quality test set.
*Deliverable:* ask a question in plain English, get genuinely relevant passages
with page and section. Measurably better than the keyword version.

### Month 3 — Grounded answers and summaries
*Learn:* the Claude API · system prompts · prompt engineering · grounding vs.
hallucination · the citations feature · streaming · token counting · prompt
caching · map-reduce summarising.
*Build:* answer engine with citations · refusal behaviour when unsupported ·
section summaries · executive summary · response caching · cost tracking.
*Deliverable:* **the core demo** — a working cited RAG system on the command
line. This is the heart of the project; everything after is platform and
features.

### Month 4 — Backend and database
*Learn:* HTTP and REST · FastAPI · SQL · schema design · SQLAlchemy · Pydantic
· async Python · background jobs · Docker basics.
*Build:* PostgreSQL schema (documents, chunks, figures, risks, findings,
users) · FastAPI service · upload endpoint · background ingestion worker with
job status · search and ask endpoints · auto-generated API docs. Install
Node.js this month.
*Deliverable:* a running API — upload a PDF over HTTP, watch it ingest, ask a
question, get a cited JSON answer.
*Academic:* midterm progress report and demo.

### Month 5 — Frontend
*Learn:* HTML/CSS/JS basics · React (components, props, state, effects) ·
calling an API from the browser · routing · Tailwind · PDF.js.
*Build:* React app — document library · upload with progress · document
dashboard · ask screen with streaming answers · **citation chips that open the
PDF at the cited page**.
*Deliverable:* **first end-to-end demo.** Upload in the browser, ask a
question, get a cited answer, click the citation, land on the page.

### Month 6 — Structured extraction
*Learn:* structured outputs and JSON schemas · vision/multimodal prompting ·
PDF table extraction · data validation · normalising financial numbers.
*Build:* financial indicator extraction (vision on statement pages) into the
database · risk factor extraction and categorisation · financials screen with a
multi-year table · risks screen grouped by category.
*Deliverable:* open a prospectus and see its financials and risks as structured
data, every cell citing its page.

### Month 7 — The agent and the verification engine
*Learn:* tool use / function calling · the agent loop · when an agent beats a
fixed pipeline · pytest · deterministic checks.
*Build:* tool-using agent with `search_document`, `get_page`, `lookup_figure`,
`list_sections` · missing-section checker · conflicting-figure detector ·
year-over-year change analysis · findings persisted and flagged on the
dashboard.
*Deliverable:* the standout feature — ask "are the revenue figures consistent?"
and watch the system plan and run a multi-step investigation, then cite it.

### Month 8 — Comparison, report, and access control
*Learn:* diffing structured data · orchestrating parallel LLM calls · report
templating · PDF/DOCX generation · authentication and roles.
*Build:* revised-vs-earlier version comparison · sector peer comparison ·
preliminary report generator (parallel specialist passes) with download · login
and reviewer/admin roles.
*Deliverable:* all ten functional requirements working through the web app.

### Month 9 — Evaluation, deployment, and defence
*Learn:* evaluation sets · LLM-as-judge · retrieval metrics · measuring
citation accuracy and hallucination rate · Docker Compose · deployment ·
technical writing.
*Build:* evaluation harness and results tables · bug fixing and UI polish ·
Arabic and scanned-page handling · docker-compose deployment · final report ·
demo video · defence presentation.
*Deliverable:* a deployed, measured, documented system and a defence.

---

## Scope control

**Must ship** (the project fails without these): ingestion, semantic retrieval,
cited Q&A, financial extraction, risk extraction, missing-section and conflict
checks, the web interface, the report, the evaluation.

**Cut first if behind schedule**, in this order: sector peer comparison ·
Arabic support · auth roles beyond a single login · cloud deployment (demo
locally) · the agent (fall back to fixed pipelines for the checks).

**Never cut:** citations. They are the project's thesis.

**Buffer:** treat Month 9 as evaluation and writing only. Do not plan features
into it. Every senior project overruns.

---

## Working agreements

- **One step at a time.** Finish it, run it, understand it, then move on.
- **Every month ends with a runnable demo.**
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

**Month 1, in progress.** An early ingestion script and a throwaway keyword
search exist in `search_prospectus.py`, written before setup. The keyword
search is scaffolding — it gets absorbed into the hybrid retriever in Month 2.
Project setup (venv, git, structure) still to do.

Files: `prospectus.pdf`, `search_prospectus.py`, `CLAUDE.md`.
