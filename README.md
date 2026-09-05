# AI-Powered Prospectus Analysis and Review System

Senior project for the Capital Market Authority (CMA). An LLM-powered platform
that reads a company prospectus, answers reviewer questions in plain language,
extracts financial indicators and risk factors, checks for missing sections and
conflicting figures — and **cites the page and section behind every answer**.

See [CLAUDE.md](CLAUDE.md) for the full architecture and nine-month plan.

## Setup

```bash
# 1. Create the virtual environment
python -m venv .venv

# 2. Activate it
#    Windows PowerShell:  .venv\Scripts\Activate.ps1
#    Git Bash:            source .venv/Scripts/activate
#    macOS / Linux:       source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your settings file and add your API key
cp .env.example .env
```

## Usage

```bash
# List the prospectuses found
python -m src.ingest --list

# Ingest everything: text, sections, page numbers, chunks
python -m src.ingest

# One market only
python -m src.ingest --market sukuk

# Also render pages as images (for vision work later)
python -m src.ingest --images 1-10
python -m src.ingest --images all --dpi 200

# Search the ingested library (keyword only, for now)
python -m src.search "risks related to liquidity"
python -m src.search "capital adequacy" --market sukuk --top 3
```

Output goes to `data/` (git-ignored — regenerate by re-running the script).

## Project layout

| Path | Contents |
|---|---|
| `sukuk/`, `tasi/`, `nomu/` | Prospectus PDFs — the folder sets the market |
| `src/config.py` | All paths and settings in one place |
| `src/documents.py` | Finds the PDFs, gives each a stable id |
| `src/ingest.py` | Orchestrates ingestion; text and page images |
| `src/pagemap.py` | Works out the page number *printed* on each page |
| `src/sections.py` | Document outline, from bookmarks or font analysis |
| `src/boilerplate.py` | Strips running headers and footers |
| `src/chunks.py` | Cuts pages into passages carrying full citations |
| `data/pages/` | Extracted text + outline, as JSON |
| `data/chunks/` | Citable chunks, as JSON |
| `data/images/` | Rendered page images (PNG) |
| `src/search.py` | Keyword search over the library — the Phase 3 baseline |

## The library

The CMA runs three offering regimes, each with its own required disclosures.
A PDF's market is set by the folder it sits in.

| Market | Document | Pages | Chunks |
|---|---|---|---|
| `sukuk/` | Riyad Bank Sukuk Offering Prospectus | 195 | 889 |
| `tasi/` | Naseej International Trading — Rights Issue | 258 | 1,219 |
| `nomu/` | Jamjoom Fashion Trading Company | 408 | 1,305 |

**Page numbers.** The number printed on a page does not match the PDF page
count — the gap is 22, 41 and 43 respectively, caused by unnumbered front
matter. `pagemap.py` detects it per document rather than hard-coding it, and
every chunk carries both numbers so citations point where a reviewer actually
looks.

## Status

Phases 1-2 complete: ingestion, structure and citable chunks.
Next: Phase 3 — embeddings and retrieval.
