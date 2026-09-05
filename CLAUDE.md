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

## Priority: the core must be excellent before the edges are broad

All ten requirements ship — the list is fixed. But they are **not equally
important**, and effort is allocated accordingly.

**Tier 1 — the project is judged on these.** Executive summaries (1),
question answering (2), and citations (5). The bar is *correct answers that
are not stupid, with sources*. Quality here beats every other feature.

**Tier 2 — substantial features, normal quality bar.** Financial indicator
extraction (3), risk factors (4), missing sections (7), conflicting figures
(8), year-over-year changes (6), the preliminary report (10).

**Tier 3 — build it, do not gold-plate it.** Comparison (9), both modes.
Required, but the last place to spend an extra week.

Two consequences that change the plan:

- **Retrieval quality is the whole ballgame.** A wrong or vague answer is worse
  than useless for a regulator, and it costs reviewer time rather than saving
  it. Months 2 and 3 carry the most weight of any months in the project.
- **Evaluation starts in Month 2, not Month 9.** "Answers that are not stupid"
  cannot be improved unless it is measured. A golden question set is built
  early and re-run continuously as a regression test. Month 9 then becomes
  final measurement and write-up rather than first measurement.

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

Built in Month 2 alongside retrieval, re-run after every change to chunking,
retrieval or prompts. Its purpose is regression detection, not a final grade:
it tells you whether a change made the system better or worse, which is
otherwise impossible to know.

### Required-disclosures checklist

The user can obtain the **official CMA disclosure requirements for a sukuk
offering**. Requirement 7 must be built against that real list rather than a
list inferred from the sample document's own table of contents — an inferred
checklist can only ever find sections the document already has. Obtain it
before Month 7; earlier is better, as it also informs what the Month 3 summary
should highlight.

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
| Embeddings | dedicated embedding model — chosen in Month 2 | English-only; local open model vs. hosted |
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

**More documents needed — now a hard blocker, not a nice-to-have.** Both
comparison modes are must-ship, so the demo needs a minimum of three documents
and ideally four:

| # | Document | Enables |
|---|---|---|
| 1 | Riyad Bank Sukuk Offering Prospectus | have it |
| 2 | Another Riyad Bank prospectus from a different period | same-company-over-time comparison |
| 3 | Another Saudi bank's sukuk prospectus | cross-company sector comparison |
| 4 | Any further prospectus | makes the library feel real in the demo |

Without #2 and #3 two must-ship requirements cannot be demonstrated at all.
Collect these during Months 1-3. This is the single most likely way the project
loses features.

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
*Build:* chunking with metadata · embedding pipeline (**English-only model** —
Arabic is out of scope) · vector index · hybrid retriever · LLM reranker · a
retrieval quality test set.
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
users, conversations, messages — saved chat history is must-ship) · FastAPI service · upload endpoint · background ingestion worker with
job status · search and ask endpoints · auto-generated API docs. Install
Node.js this month.
*Deliverable:* a running API — upload a PDF over HTTP, watch it ingest, ask a
question, get a cited JSON answer.
*Academic:* midterm progress report and demo.

### Month 5 — Frontend
*Learn:* HTML/CSS/JS basics · React (components, props, state, effects) ·
calling an API from the browser · routing · Tailwind · PDF.js.
*Build:* React chat app — message thread with streaming answers · upload with
ingestion progress · **citation chips that open the PDF in a pane beside the
conversation** · the proactive opening briefing · mode switcher scaffolding
(Ask / Review / Compare).
*Deliverable:* **first end-to-end demo.** Upload in the browser, watch the
assistant open with its briefing, ask a follow-up question, click a citation,
see the source page appear beside the answer.

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
*Build:* **Compare mode** — the same company's prospectus across different time
periods, answered in the same conversation rather than a separate screen ·
cross-company sector comparison (equally must-ship) · preliminary report generator (parallel
specialist passes) with download · login and reviewer/admin roles.
*Deliverable:* all ten functional requirements reachable through the
conversation.

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

**Must ship** (the project fails without these): ingestion · semantic retrieval
· cited Q&A in a chat interface · the proactive opening briefing · financial
extraction · risk extraction · missing-section and conflict checks · **both
comparison modes — same company across time periods AND cross-company sector
comparison** · reviewer accounts with saved conversation history · the report ·
the evaluation.

**Cut first if behind schedule**, in this order: cloud deployment (demo
locally) · admin role as distinct from reviewer · the report as a downloadable
file (show it in the chat instead) · the agent (fall back to fixed pipelines
for the checks).

**Explicitly out of scope:** Arabic support. English only. If the project
finishes early it may be added, but nothing is designed around it. Switching to
a multilingual embedding model later costs one re-indexing run — minutes and
cents for a handful of documents — so deferring this is cheap.

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
