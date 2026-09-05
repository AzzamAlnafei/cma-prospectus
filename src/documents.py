"""
documents.py -- find the prospectuses and give each one a stable identity.

WHY THIS FILE EXISTS
    The system holds a LIBRARY of prospectuses, not one file. Before anything
    can be extracted, we need to know which documents exist, which market each
    belongs to, and what to call it.

    The name matters more than it looks. Every chunk of text, every extracted
    figure and every risk factor will carry a document_id. If that id changes
    -- because it was built from something unstable -- everything already
    stored points at a document that no longer exists.
"""

import re

from src import config


def slugify(text):
    """
    Turn a filename into a safe, stable id.

        "Jamjoom_Fashion_Trading_Company_en"  ->  "jamjoom-fashion-trading-company-en"

    Lowercase, and anything that is not a letter or digit becomes a hyphen.
    This keeps ids usable in URLs and filenames later without escaping.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)   # runs of junk -> one hyphen
    return text.strip("-")


def discover_documents():
    """
    Look inside each market folder and return one record per PDF found:

        [{"document_id": "sukuk-prospectus",
          "market": "sukuk",
          "path": Path(".../sukuk/prospectus.pdf"),
          "filename": "prospectus.pdf"}, ...]

    The market comes from the folder name, so filing a new prospectus is just
    dropping the PDF into sukuk/, tasi/ or nomu/ -- no code change needed.

    The id includes the market, so two documents with the same filename in
    different markets can never collide.
    """
    documents = []

    for market in config.MARKETS:
        market_dir = config.PROJECT_ROOT / market

        if not market_dir.is_dir():
            continue

        # sorted() so the order is the same on every run. Anything that varies
        # between runs makes bugs harder to reproduce.
        for pdf_path in sorted(market_dir.glob("*.pdf")):
            documents.append({
                "document_id": f"{market}-{slugify(pdf_path.stem)}",
                "market": market,
                "path": pdf_path,
                "filename": pdf_path.name,
            })

    return documents


def find_document(document_id):
    """Return one document record by its id, or None if there is no such id."""
    for document in discover_documents():
        if document["document_id"] == document_id:
            return document
    return None
