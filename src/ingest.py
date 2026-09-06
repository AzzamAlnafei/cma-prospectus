"""
ingest.py -- turn every prospectus in the library into structured, citable data.

WHAT THIS DOES, PER DOCUMENT
    1. Extract the text of every page.
    2. Work out which number is PRINTED on each page (they disagree with the
       PDF's own page numbers).
    3. Build the section outline, from the PDF's bookmarks or from the way
       headings are typeset.
    4. Cut the pages into overlapping passages, each carrying document, market,
       both page numbers, and its section.
    5. Optionally render pages as PNG images, for the vision work later.
    6. Save it all as JSON you can open and inspect.

WHY EVERYTHING CARRIES SO MUCH METADATA
    Our standing rule is that every answer cites its page and section. Metadata
    attached at extraction time survives all the way to the reviewer's screen.
    Metadata bolted on later never quite does.

HOW TO RUN IT
    python -m src.ingest                       # every document, text only
    python -m src.ingest --market sukuk        # one market only
    python -m src.ingest --images 1-10         # also render pages 1 to 10
    python -m src.ingest --list                # just show what was found
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import pymupdf

# ---------------------------------------------------------------------------
# Let this file be run BOTH ways:
#     python -m src.ingest          <- the normal way
#     python src/ingest.py          <- e.g. the Run button in VS Code
#
# Running a file by its path puts that file's OWN folder (src/) at the front
# of Python's import path, so "from src import ..." fails -- Python is stood
# inside src/ looking for a folder called src. Adding the project root fixes
# it. __package__ is empty only when the file was run directly, so this does
# nothing in the normal case.
# ---------------------------------------------------------------------------
if __name__ == "__main__" and not __package__:
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import boilerplate
from src import chunks as chunking
from src import config, documents, pagemap, sections


# ---------------------------------------------------------------------------
# Step 1: extract the text
# ---------------------------------------------------------------------------

def extract_pages(doc):
    """
    Read every page and return:
        [{"page": 1, "text": "...", "char_count": 4842}, ...]

    Page numbers here count from 1, matching what a human sees in a PDF reader.
    Converting once, here, means every page number downstream is already the
    one a reviewer would recognise.
    """
    pages = []

    for index, page in enumerate(doc):
        # get_text returns "" rather than None for a page with no text layer,
        # but we guard anyway -- a full-page image returns nothing useful.
        text = page.get_text("text") or ""
        pages.append({
            "page": index + 1,
            "text": text,
            "char_count": len(text),
        })

    return pages


# ---------------------------------------------------------------------------
# Step 2: render page images (optional)
# ---------------------------------------------------------------------------

def parse_page_range(spec, page_count):
    """
    Turn a page selection into a list of page numbers.

        "all"       -> [1, 2, ... page_count]
        "1-10"      -> [1, 2, ... 10]
        "12,88,91"  -> [12, 88, 91]

    Pages outside the document are dropped rather than crashing: a typo should
    not lose you a long extraction run.
    """
    if spec.strip().lower() == "all":
        return list(range(1, page_count + 1))

    wanted = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, _, end_text = part.partition("-")
            wanted.update(range(int(start_text), int(end_text) + 1))
        else:
            wanted.add(int(part))

    return sorted(p for p in wanted if 1 <= p <= page_count)


def render_page_images(doc, document_id, page_numbers, dpi=150):
    """
    Save chosen pages as PNG files.

    WHY: a financial statement is a table, and extracted as text a table becomes
    a soup of numbers with the rows and columns lost. Claude can look at a
    picture of the page and see the table as a table.

    dpi is dots per inch -- how much detail. 150 is readable for small print in
    a financial table while keeping files a few hundred KB.
    """
    written = []

    for page_number in page_numbers:
        pixmap = doc[page_number - 1].get_pixmap(dpi=dpi)
        # Zero-padded so files sort correctly: page_009 before page_010.
        output_path = config.IMAGES_DIR / f"{document_id}_page_{page_number:03d}.png"
        pixmap.save(output_path)
        written.append(output_path)

    return written


# ---------------------------------------------------------------------------
# Step 3: process one document end to end
# ---------------------------------------------------------------------------

def ingest_document(document, image_spec=None, dpi=150):
    """Run the whole pipeline for a single prospectus and save its output."""
    document_id = document["document_id"]
    market = document["market"]

    print(f"\n{'=' * 74}")
    print(f"{document_id}   [{market}]   {document['filename']}")
    print("=" * 74)

    with pymupdf.open(document["path"]) as doc:
        # --- text ---
        pages = extract_pages(doc)
        page_count = len(pages)
        total_chars = sum(p["char_count"] for p in pages)
        empty_pages = [p["page"] for p in pages if p["char_count"] == 0]

        print(f"  pages           : {page_count}")
        print(f"  characters      : {total_chars:,}")

        if empty_pages:
            print(f"  EMPTY pages     : {len(empty_pages)} -> {empty_pages[:12]}")
            print("     (no text layer -- probably scanned images, will need OCR)")
        else:
            print("  empty pages     : none -- full text layer, no OCR needed")

        # --- printed page numbers ---
        page_texts = [p["text"] for p in pages]
        offset, confidence = pagemap.detect_page_offset(page_texts)
        print(f"  {pagemap.describe(offset, confidence, page_count)}")

        # --- sections ---
        outline, outline_source = sections.build_outline(doc)
        print(f"  sections        : {len(outline)} (source: {outline_source})")
        for section in outline[:4]:
            print(f"       L{section['level']} p{section['start_page']:>4}  {section['title'][:52]}")
        if len(outline) > 4:
            print(f"       ... and {len(outline) - 4} more")

        index = sections.section_index(outline, page_count)

        # --- strip running headers and footers ---
        # This must happen AFTER the page-offset detection above, because the
        # page numbers hidden inside those headers are the evidence it needs.
        furniture = boilerplate.find_boilerplate_lines(page_texts)
        cleaned_pages = boilerplate.clean_pages(pages, furniture)
        removed_chars = total_chars - sum(p["char_count"] for p in cleaned_pages)
        print(f"  boilerplate     : {len(furniture)} repeating line(s) removed "
              f"({removed_chars:,} chars, {removed_chars / max(total_chars, 1):.1%})")

        # --- chunks ---
        chunk_list = chunking.chunk_document(
            cleaned_pages, document_id, market, offset, index
        )
        with_printed = sum(1 for c in chunk_list if c["printed_page"] is not None)
        print(f"  chunks          : {len(chunk_list)} "
              f"({with_printed} with a printed page number)")

        # --- images ---
        if image_spec:
            page_numbers = parse_page_range(image_spec, page_count)
            written = render_page_images(doc, document_id, page_numbers, dpi=dpi)
            size_mb = sum(p.stat().st_size for p in written) / (1024 * 1024)
            print(f"  images          : {len(written)} rendered at {dpi} dpi ({size_mb:.1f} MB)")

    # --- save ---
    extracted_at = datetime.now(timezone.utc).isoformat()

    pages_payload = {
        "document_id": document_id,
        "market": market,
        "source_file": document["filename"],
        "page_count": page_count,
        "page_offset": offset,
        "page_offset_confidence": round(confidence, 3),
        "outline_source": outline_source,
        "extracted_at": extracted_at,
        "outline": outline,
        "pages": pages,
    }
    pages_path = config.PAGES_DIR / f"{document_id}.json"
    _write_json(pages_path, pages_payload)

    chunks_payload = {
        "document_id": document_id,
        "market": market,
        "chunk_count": len(chunk_list),
        "extracted_at": extracted_at,
        "chunks": chunk_list,
    }
    chunks_path = config.CHUNKS_DIR / f"{document_id}.json"
    _write_json(chunks_path, chunks_payload)

    print(f"  saved           : {pages_path.name} + {chunks_path.name}")

    # Show one real citation, so the point of all this is visible.
    if chunk_list:
        sample = chunk_list[len(chunk_list) // 2]
        print(f"  sample citation : {chunking.citation_for(sample)}")

    return {"document_id": document_id, "chunks": len(chunk_list),
            "pages": page_count, "offset": offset, "outline_source": outline_source}


def _write_json(path, payload):
    """
    ensure_ascii=False keeps typographic and Arabic characters readable in the
    file rather than turning them into \\u escape codes.
    indent=2 makes it inspectable, which matters more here than file size.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract text, structure and citable chunks from prospectus PDFs."
    )
    parser.add_argument("--market", choices=config.MARKETS,
                        help="process one market only (default: all)")
    parser.add_argument("--document", help="process one document_id only")
    parser.add_argument("--images", metavar="PAGES",
                        help='render pages as PNG: "all", "1-10", or "12,88,91"')
    parser.add_argument("--dpi", type=int, default=150,
                        help="image resolution when rendering (default: 150)")
    parser.add_argument("--list", action="store_true",
                        help="list the documents found and exit")
    args = parser.parse_args()

    # Windows terminals default to an old character set that cannot display the
    # curly apostrophes in these documents. This affects PRINTING only -- the
    # extracted data is correct either way.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    found = documents.discover_documents()

    if not found:
        print("No PDFs found. Expected them in: "
              + ", ".join(f"documents/{m}/" for m in config.MARKETS))
        sys.exit(1)

    if args.market:
        found = [d for d in found if d["market"] == args.market]
    if args.document:
        found = [d for d in found if d["document_id"] == args.document]

    if args.list:
        print(f"{len(found)} document(s):")
        for d in found:
            print(f"  {d['market']:6}  {d['document_id']:45}  {d['filename']}")
        return

    config.ensure_directories()

    results = [ingest_document(d, image_spec=args.images, dpi=args.dpi)
               for d in found]

    print(f"\n{'=' * 74}")
    print(f"LIBRARY: {len(results)} document(s), "
          f"{sum(r['chunks'] for r in results):,} chunks total")
    print("=" * 74)


if __name__ == "__main__":
    main()
