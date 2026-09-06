"""
chunks.py -- cut pages into small passages, each carrying a full citation.

WHY CHUNK AT ALL
    Next phase turns every passage into a vector so the system can search by
    meaning. A whole page is roughly 800 words covering several unrelated
    topics, and a vector for it ends up representing an average of all of them
    -- which matches nothing well. Smaller passages are about one thing, so
    their vectors are sharp.

WHY CHUNKS NEVER CROSS A PAGE BOUNDARY
    This is the important design decision in this file. A chunk that spanned
    pages 87 and 88 could not honestly cite either one. Since every answer must
    carry a page, the page is the natural ceiling for a chunk. We accept a
    slightly awkward cut at the bottom of each page in exchange for a citation
    that is always exactly right.

WHY THEY OVERLAP
    Windows advance by fewer words than they contain, so consecutive chunks
    share text. Without overlap, a sentence unlucky enough to land on a
    boundary gets sliced in half and matches nothing properly.
"""

from src import pagemap


# Chunk size in words. Small enough to be about one topic; large enough to
# carry the context a reader needs to understand it.
WORDS_PER_CHUNK = 180

# How far each window advances. Lower than WORDS_PER_CHUNK, so chunks overlap
# by (180 - 120) = 60 words, a third of a chunk.
WORDS_TO_ADVANCE = 120

# Below this, a leftover at the bottom of a page is a page number or a footer,
# never an answer.
MIN_CHUNK_WORDS = 25


def chunk_document(pages, document_id, market, page_offset, section_index):
    """
    Turn extracted pages into a list of chunks, each with a full citation.

    Every chunk looks like:

        {"chunk_id":     "sukuk-riyad-bank-en-p136-c0",
         "document_id":  "sukuk-riyad-bank-en",
         "market":       "sukuk",
         "pdf_page":     136,
         "printed_page": 114,
         "section":      "Management committees",
         "section_path": "CORPORATE GOVERNANCE > Management committees",
         "text":         "..."}

    Both page numbers travel together from here to the reviewer's screen:
    pdf_page opens the file at the right place, printed_page is what a human
    is told.
    """
    chunks = []

    for page in pages:
        pdf_page = page["page"]

        # .split() with no argument splits on any whitespace and drops the
        # empties, which conveniently cleans up the messy line breaks PDFs are
        # full of.
        words = page["text"].split()
        if not words:
            continue

        printed_page = pagemap.printed_page_for(pdf_page, page_offset)

        section = section_index[pdf_page - 1] if pdf_page <= len(section_index) else None
        section_title = section["title"] if section else None
        section_path = section["path"] if section else None

        # Walk the page in overlapping windows.
        position = 0
        for chunk_number, start in enumerate(range(0, len(words), WORDS_TO_ADVANCE)):
            window = words[start:start + WORDS_PER_CHUNK]

            if len(window) < MIN_CHUNK_WORDS:
                continue

            chunks.append({
                "chunk_id": f"{document_id}-p{pdf_page}-c{chunk_number}",
                "document_id": document_id,
                "market": market,
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "section": section_title,
                "section_path": section_path,
                "text": " ".join(window),
            })

            position = start

            # If this window already reached the end of the page, stop -- the
            # next window would repeat the tail with nothing new in it.
            if start + WORDS_PER_CHUNK >= len(words):
                break

    return chunks


def citation_for(chunk):
    """
    Format a chunk's citation the way a reviewer should see it.

        "page 114, Management committees"
        "PDF page 4, Front matter"   <- when no printed number exists

    Being explicit about "PDF page" when the printed number is unknown matters:
    it tells the reviewer which numbering to use rather than quietly handing
    them a number that will not match their copy.
    """
    if chunk["printed_page"] is not None:
        where = f"page {chunk['printed_page']}"
    else:
        where = f"PDF page {chunk['pdf_page']}"

    if chunk["section"]:
        return f"{where}, {chunk['section']}"
    return where
