"""
config.py -- one place for every path and setting in the project.

WHY THIS FILE EXISTS
    Without it, "where is the PDF?" gets answered separately in every script,
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
#   .resolve()  turns it into a full path
#   .parent     -> src/
#   .parent     -> the project root
# Building paths this way means the project works no matter which folder you
# happen to be standing in when you run it.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = PROJECT_ROOT / "prospectus.pdf"

DATA_DIR = PROJECT_ROOT / "data"
PAGES_DIR = DATA_DIR / "pages"      # extracted text, as JSON
IMAGES_DIR = DATA_DIR / "images"    # rendered page pictures, as PNG


# ---------------------------------------------------------------------------
# Settings from .env
# ---------------------------------------------------------------------------

# load_dotenv() reads the .env file and copies its contents into the
# "environment" -- a set of named values the operating system hands to your
# program. The key is then available to Python, but exists nowhere in the code
# and so can never be committed to git by accident.
load_dotenv(PROJECT_ROOT / ".env")

# os.getenv returns None if the name is not set, instead of crashing.
# We do not require the key yet -- ingestion never calls the API.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")


def ensure_directories():
    """
    Create the data folders if they do not already exist.

    parents=True   also create any missing parent folder
    exist_ok=True  do nothing (instead of crashing) if it is already there
    """
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
