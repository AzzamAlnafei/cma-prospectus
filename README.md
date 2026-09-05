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
# Extract all text, page by page
python -m src.ingest

# Also render specific pages as images
python -m src.ingest --images 1-10
python -m src.ingest --images 12,88,91
python -m src.ingest --images all --dpi 200
```

Output goes to `data/` (git-ignored — regenerate it by re-running the script).

## Project layout

| Path | Contents |
|---|---|
| `src/config.py` | All paths and settings in one place |
| `src/ingest.py` | PDF → text per page + rendered page images |
| `data/pages/` | Extracted text as JSON |
| `data/images/` | Rendered page images (PNG) |
| `tests/` | Automated tests |
| `search_prospectus.py` | Early keyword-search prototype — replaced in Month 2 |

## Sample document

`prospectus.pdf` — Riyad Bank Sukuk Offering Prospectus, 195 pages, full text
layer (no OCR needed).

**Note:** printed page numbers run 22 behind PDF page numbers (PDF page 136 is
printed page 114). Citations must report the printed number a reviewer sees.

## Status

Month 1 — ingestion working.
