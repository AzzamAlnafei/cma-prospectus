"""
pagemap.py -- work out the page number PRINTED on each page.

THE PROBLEM
    A PDF reader counts pages from 1. The number printed on the page usually
    does not agree, because prospectuses open with unnumbered front matter --
    covers, notices, contents. In our sample documents:

        sukuk : PDF page 136  shows  "114"   (offset 22)
        nomu  : PDF page  87  shows   "44"   (offset 43)
        tasi  : PDF page  60  shows   "19"   (offset 41)

WHY IT MATTERS ENOUGH TO GET ITS OWN FILE
    Our standing rule is that every answer cites its page. If the system tells
    a reviewer "see page 136" and they open their copy to page 136, they land
    22 pages away from the answer. Nothing errors. Nothing looks broken. The
    citation is technically correct and completely useless -- which is the
    worst kind of bug, because you only find it by checking.

    So we keep BOTH numbers:
        pdf_page      -- for opening the file at the right place
        printed_page  -- for anything a human reads

HOW WE FIND THE OFFSET
    We do not hard-code 22. We work it out, per document, from evidence.

    For every page we collect numbers that look like page numbers, and for each
    one compute what the offset WOULD be. The true offset is then whichever
    value shows up on the most pages. One page might mention "22" for some
    unrelated reason; it will not do so consistently on 170 pages.

    Two printing styles both have to work:
        sukuk, nomu : the number sits alone on its own line      -> "114"
        tasi        : it is tacked onto the running header       -> "... Company | 19"
    Reading the first and last few lines of the page catches both.
"""

import re
from collections import Counter


# How many lines from the top and bottom of a page to inspect. Page numbers
# live in headers and footers, never in the middle of a paragraph.
LINES_TO_INSPECT = 3

# The offset is only trusted if it shows up on at least this share of pages.
# Below that we are pattern-matching noise, and a wrong page number is worse
# than an honest "unknown".
MIN_CONFIDENCE = 0.35


def _candidate_numbers(page_text):
    """
    Pull plausible page numbers out of the top and bottom of one page.

    Returns a set, because a number appearing twice on one page is still only
    one piece of evidence.
    """
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]
    if not lines:
        return set()

    edges = lines[:LINES_TO_INSPECT] + lines[-LINES_TO_INSPECT:]

    # A line that is nothing but a number is a page number wherever it appears.
    # We need this because PDF text does not always come out in visual order:
    # the Nomu document's footer lands in the MIDDLE of its extracted text, so
    # looking only at the first and last lines missed it on every single page.
    standalone = [line for line in lines if re.fullmatch(r"\d{1,3}", line)]

    numbers = set()
    for line in edges + standalone:
        # Ignore long lines: a page number never sits inside a paragraph.
        # 120 characters is generous enough for a running header like
        # "Rights Issue Prospectus Naseej International Trading Company | 19".
        if len(line) > 120:
            continue

        # \b...\b are word boundaries, so "2024G" and "1446H" do not match --
        # which matters here, because these documents are full of Hijri and
        # Gregorian years that would otherwise pollute the evidence.
        for match in re.findall(r"\b(\d{1,3})\b", line):
            numbers.add(int(match))

    return numbers


def detect_page_offset(page_texts):
    """
    Given the text of every page in order, return:

        (offset, confidence)

    where printed_page = pdf_page - offset, and confidence is the share of
    pages that agreed. Returns (None, 0.0) when no offset is trustworthy.
    """
    votes = Counter()

    for index, text in enumerate(page_texts):
        pdf_page = index + 1

        for number in _candidate_numbers(text):
            offset = pdf_page - number

            # A negative offset would mean the printed number runs AHEAD of the
            # PDF page, which cannot happen -- front matter only ever pushes
            # printed numbers behind. An absurdly large offset is noise.
            if 0 <= offset < len(page_texts):
                votes[offset] += 1

    if not votes:
        return None, 0.0

    offset, agreeing_pages = votes.most_common(1)[0]
    confidence = agreeing_pages / len(page_texts)

    if confidence < MIN_CONFIDENCE:
        return None, confidence

    return offset, confidence


def printed_page_for(pdf_page, offset):
    """
    Convert a PDF page number into the number printed on that page.

    Returns None when there is no printed number -- either because we could not
    determine the offset at all, or because this page is front matter that sits
    before the numbering starts. Returning None is the honest answer, and the
    reviewer-facing layer can then say "PDF page 4" rather than inventing
    "page -18".
    """
    if offset is None:
        return None

    printed = pdf_page - offset
    return printed if printed >= 1 else None


def describe(offset, confidence, page_count):
    """A one-line human-readable summary, for the ingestion report."""
    if offset is None:
        return (f"printed page numbers: NOT DETECTED "
                f"(best agreement {confidence:.0%}) -- citations will use PDF pages")

    first_numbered = offset + 1
    return (f"printed page numbers: PDF page - {offset} "
            f"({confidence:.0%} of pages agree; numbering starts at PDF page "
            f"{first_numbered} of {page_count})")
