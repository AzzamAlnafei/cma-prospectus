"""
config.py -- one place for every path and setting in the project.

WHY THIS FILE EXISTS
    Without it, "where are the PDFs?" gets answered separately in every script,
    and the day you move a folder you have to hunt down all of them. Every
    other file imports its paths from here instead of inventing its own.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# __file__ is this file (src/config.py).
#   .resolve()  -> full path
#   .parent     -> src/
#   .parent     -> the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
PAGES_DIR = DATA_DIR / "pages"      # extracted text, as JSON
CHUNKS_DIR = DATA_DIR / "chunks"    # chunked text with citations, as JSON
IMAGES_DIR = DATA_DIR / "images"    # rendered page pictures, as PNG


# ---------------------------------------------------------------------------
# Markets
# ---------------------------------------------------------------------------
#
# The CMA runs three different offering regimes, and each has its OWN list of
# required disclosures. A prospectus is filed under exactly one of them, so the
# market decides which checklist and which financial indicators apply.
#
#   sukuk  Islamic bonds -- debt, not shares
#   tasi   the Main Market. Largest companies, heaviest disclosure requirements
#   nomu   the Parallel Market. Smaller companies, lighter requirements
#
# We take the market from the FOLDER a PDF sits in. That is deliberately
# simple: a human filing the document already knows which market it belongs
# to, so guessing it from the text would add a chance of being wrong for no
# benefit.
MARKETS = ("sukuk", "tasi", "nomu")


# ---------------------------------------------------------------------------
# Settings from .env
# ---------------------------------------------------------------------------

# load_dotenv() reads the .env file and copies its contents into the
# "environment" -- a set of named values the operating system hands to your
# program. The key is then available to Python but exists nowhere in the code,
# so it can never be committed to git by accident.
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")


def ensure_directories():
    """Create the data folders if they do not already exist."""
    for directory in (PAGES_DIR, CHUNKS_DIR, IMAGES_DIR):
        directory.mkdir(parents=True, exist_ok=True)
