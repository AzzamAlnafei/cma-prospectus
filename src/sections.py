"""
sections.py -- work out which section each page belongs to.

WHY THIS MATTERS
    Our citation rule is "page AND section". A page number alone tells a
    reviewer where to look but not what they are looking at. "Page 114,
    Corporate Governance" is a citation; "page 114" is a coordinate.

TWO WAYS TO FIND SECTIONS, AND WHY WE NEED BOTH
    Many PDFs carry a built-in outline -- the clickable bookmarks a PDF reader
    shows in its sidebar. When it is good it is perfect: real section titles,
    real hierarchy, real page numbers, no guessing.

    But it is only as good as whoever produced the file, and our three
    documents show the whole range:

        tasi   excellent -- "2-1-1 Risks related to revenue concentration"
        nomu   good, but buried in 165 exhibit and table captions
        sukuk  useless -- Word leftovers like "_Hlk193295001" and "bmkStart"

    So the rule is: TRY THE OUTLINE, VERIFY IT, AND FALL BACK IF IT IS JUNK.
    Trusting it blindly would give the sukuk document sections named after
    Microsoft Word's internal bookmarks.

    The fallback reads the actual formatting. In the sukuk document the body
    text is 8pt and headings are BOLD at 10pt and 12pt -- so "bold and bigger
    than the body text" finds them. Usefully, the page number is also 12pt but
    NOT bold, so requiring bold excludes it for free.
"""

import re
from collections import Counter


# Outline entries that are not real sections.
#   Exhibit(/Table(/Figure(  -- captions, not sections (165 of them in nomu)
#   _Hlk, _Toc, _Ref, bmk    -- Microsoft Word internal bookmarks
#   _cp_change, Brochet      -- other authoring-tool leftovers
JUNK_TITLE_PATTERNS = [
    re.compile(r"^(exhibit|table|figure)\s*\(", re.IGNORECASE),
    re.compile(r"^(_hlk|_toc|_ref|_cp_|bmk|ole_|brochet)", re.IGNORECASE),
]

# A usable outline needs enough real entries to actually divide the document.
MIN_USABLE_OUTLINE_ENTRIES = 8


def _clean_title(title):
    """Tidy whitespace, including the tab and non-breaking space these PDFs use."""
    title = title.replace("\t", " ").replace(" ", " ").replace("\xa0", " ")
    return " ".join(title.split())


def _is_junk_title(title):
    """True if this outline entry is an authoring-tool artefact or a caption."""
    title = title.strip()

    if not title or len(title) < 3:
        return True

    for pattern in JUNK_TITLE_PATTERNS:
        if pattern.match(title):
            return True

    # Names like "Presentation_of_Financial_Information" or "Marketriskmanagement"
    # are bookmark identifiers, not headings a person wrote. A real section
    # title contains spaces; these do not.
    if " " not in title and len(title) > 12:
        return True

    return False


def sections_from_outline(doc):
    """
    Build sections from the PDF's built-in bookmarks, or return [] if unusable.

    Each section is:
        {"level": 1, "title": "2- Risk Factors", "start_page": 49}
    where start_page is a PDF page number counting from 1.
    """
    try:
        outline = doc.get_toc()
    except Exception:
        # A malformed outline should cost us the outline, not the whole run.
        return []

    sections = []
    for level, title, page in outline:
        title = _clean_title(title)
        if _is_junk_title(title):
            continue
        if page < 1:
            continue
        sections.append({"level": level, "title": title, "start_page": page})

    if len(sections) < MIN_USABLE_OUTLINE_ENTRIES:
        return []

    sections.sort(key=lambda s: (s["start_page"], s["level"]))
    return sections


def sections_from_formatting(doc, max_pages=None):
    """
    Fallback: find headings by how they are typeset.

    Step 1  Work out the body text size -- the size the most CHARACTERS are set
            in. Counting characters rather than lines matters: a document has
            few heading lines but they can be long, so counting lines would
            skew the answer.
    Step 2  A heading is a short, bold line, larger than the body text.
    """
    page_count = len(doc) if max_pages is None else min(len(doc), max_pages)

    # ---- Step 1: what size is the body text? ----
    size_counts = Counter()
    for index in range(page_count):
        for block in doc[index].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size_counts[round(span["size"], 1)] += len(span["text"])

    if not size_counts:
        return []

    body_size = size_counts.most_common(1)[0][0]

    # ---- Step 2: collect headings ----
    sections = []
    for index in range(page_count):
        for block in doc[index].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                text = _clean_title("".join(s["text"] for s in spans))
                if not text or len(text) > 90:
                    continue

                # Skip pure numbers -- that is the page number, which in the
                # sukuk document is large but not bold.
                if re.fullmatch(r"[\d\s.,/-]+", text):
                    continue

                size = max(s["size"] for s in spans)

                # PyMuPDF packs style into a bitfield; bit 4 (value 16) is bold.
                # Checking the font name too catches fonts like "RBType-Bold"
                # that do not set the flag.
                is_bold = any(
                    (s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower()
                    for s in spans
                )

                if is_bold and size > body_size + 0.4:
                    # Bigger text means a more important heading.
                    level = 1 if size >= body_size + 3 else 2
                    sections.append({
                        "level": level,
                        "title": text,
                        "start_page": index + 1,
                    })

    # The same running heading can repeat on many pages; keep the first.
    seen = set()
    unique = []
    for section in sections:
        key = (section["title"].lower(), section["level"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(section)

    unique.sort(key=lambda s: (s["start_page"], s["level"]))
    return unique


def build_outline(doc):
    """
    Return (sections, source) where source explains which method was used --
    so the ingestion report can tell you honestly where the structure came from.
    """
    sections = sections_from_outline(doc)
    if sections:
        return sections, "pdf-outline"

    sections = sections_from_formatting(doc)
    if sections:
        return sections, "font-analysis"

    return [], "none"


def section_index(sections, page_count):
    """
    Pre-compute, for every PDF page, which section it falls in.

    Returns a list where entry [page - 1] is:
        {"title": ..., "path": "2- Risk Factors > 2-1 Risks Related to the Issuer"}

    Building this once is far cheaper than searching the section list again for
    every one of several thousand chunks.

    "path" carries the hierarchy, because "2-1-1 Risks related to revenue
    concentration" means much more to a reviewer when they can see it sits
    under Risk Factors.
    """
    index = [None] * page_count

    # current_by_level remembers the most recent heading seen at each depth, so
    # we can rebuild the full path when a deep subsection starts.
    current_by_level = {}
    section_position = 0

    for page in range(1, page_count + 1):
        # Apply every section that starts on or before this page.
        while (section_position < len(sections)
               and sections[section_position]["start_page"] <= page):
            section = sections[section_position]
            level = section["level"]
            current_by_level[level] = section["title"]

            # A new level-1 heading invalidates any deeper headings under the
            # previous one -- otherwise a stale subsection title would leak
            # into the next chapter's citations.
            for deeper in [lv for lv in current_by_level if lv > level]:
                del current_by_level[deeper]

            section_position += 1

        if current_by_level:
            path_parts = [current_by_level[lv] for lv in sorted(current_by_level)]
            index[page - 1] = {
                "title": path_parts[-1],
                "path": " > ".join(path_parts),
            }
        else:
            # Pages before the first heading: covers, notices, contents.
            index[page - 1] = {"title": "Front matter", "path": "Front matter"}

    return index
