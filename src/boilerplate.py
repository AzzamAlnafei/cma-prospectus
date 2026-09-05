"""
boilerplate.py -- remove the running headers and footers that repeat on
every page.

THE PROBLEM
    Extracted page text carries the furniture of the document as well as its
    content. In the TASI prospectus every single page begins with:

        "Rights Issue Prospectus Naseej International Trading Company | 14"
        "Table of Contents"

    and the sukuk document repeats "Riyad Bank Sukuk Offering Prospectus" on
    all 195 pages.

WHY IT MATTERS MORE THAN IT LOOKS
    Next phase turns every passage into a vector representing its meaning. If
    the same 12 words appear at the start of all 1,256 passages, that text is
    part of every single vector -- pushing them all slightly towards each
    other and away from what actually distinguishes them. Retrieval gets worse
    across the board, in a way that is very hard to notice.

    It also wastes tokens: boilerplate we send to Claude on every question is
    paid for on every question and adds nothing.

HOW WE FIND IT WITHOUT A LIST OF WHAT TO REMOVE
    We never hard-code "remove this bank's name". Instead: boilerplate is, by
    definition, text that repeats across many pages. So count how often each
    line appears, and drop the ones that appear nearly everywhere.

    The one wrinkle is that running headers usually contain the page number,
    so no two are byte-identical. We therefore count a NORMALISED form with
    digits replaced by "#", which makes
        "... Company | 14"  and  "... Company | 15"
    count as the same line.

IMPORTANT ORDERING
    This runs AFTER the printed-page detector, never before. The page numbers
    hidden in those headers are exactly the evidence pagemap.py needs.
"""

import re
from collections import Counter


# A line must appear on at least this share of pages to count as furniture.
# Real sentences essentially never repeat on a third of a document's pages;
# headers and footers always do.
MIN_REPEAT_SHARE = 0.30

# Long lines are content even if they somehow repeat. Headers are short.
MAX_BOILERPLATE_LENGTH = 150

# Very short documents give unreliable statistics -- two pages sharing a line
# proves nothing.
MIN_PAGES_TO_ANALYSE = 10


def _normalise(line):
    """
    Collapse a line to the form used for counting.

    Digits become "#" so that page numbers do not make every header unique,
    and case and spacing are flattened so small variations still match.
    """
    line = re.sub(r"\d+", "#", line)
    return " ".join(line.lower().split())


def find_boilerplate_lines(page_texts):
    """
    Return the set of normalised lines that look like running headers/footers.
    """
    if len(page_texts) < MIN_PAGES_TO_ANALYSE:
        return set()

    # Count PAGES a line appears on, not total occurrences -- a line printed
    # three times on one page is still evidence from only one page.
    pages_containing = Counter()

    for text in page_texts:
        seen_here = set()
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line or len(line) > MAX_BOILERPLATE_LENGTH:
                continue
            seen_here.add(_normalise(line))
        pages_containing.update(seen_here)

    threshold = len(page_texts) * MIN_REPEAT_SHARE

    return {line for line, count in pages_containing.items()
            if count >= threshold and line}


def strip_boilerplate(text, boilerplate):
    """Remove every boilerplate line from one page's text."""
    kept = []
    for raw_line in text.split("\n"):
        if _normalise(raw_line.strip()) in boilerplate:
            continue
        kept.append(raw_line)
    return "\n".join(kept)


def clean_pages(pages, boilerplate):
    """
    Return a new list of pages with boilerplate removed.

    The original page records are left untouched -- the raw text stays in
    data/pages/ so you can always see what was actually in the document, while
    the cleaned text is what gets chunked and searched. Never destroy the
    evidence you might need to debug against.
    """
    cleaned = []
    for page in pages:
        text = strip_boilerplate(page["text"], boilerplate)
        cleaned.append({**page, "text": text, "char_count": len(text)})
    return cleaned
