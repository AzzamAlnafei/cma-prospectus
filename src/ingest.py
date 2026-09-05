"""
ingest.py -- Month 1 deliverable: turn a PDF into structured data.

WHAT THIS DOES
    1. Reads every page of a PDF and extracts its text.
    2. Attaches document_id and page number to every piece of that text.
    3. Optionally renders pages as PNG images (needed for vision in Month 6,
       because financial statements are tables and tables extract badly as
       text -- but Claude can simply LOOK at the page).
    4. Saves the result as JSON you can open and inspect.

WHY document_id IS HERE ALREADY
    The system will eventually hold a LIBRARY of prospectuses, because two of
    the requirements are "compare two companies" and "compare two versions".
    Adding an id now is free. Adding it later means rewriting everything that
    ever touched a chunk of text.

WHY WE DO NOT EXTRACT SECTIONS YET
    That is the next step. This file produces page-level text; section
    detection reads that output and adds the heading each chunk sits under.
    One job per file.

HOW TO RUN IT
    python -m src.ingest                      # text only
    python -m src.ingest --images 1-10        # also render pages 1 to 10
    python -m src.ingest --images 12,88,91    # render three specific pages
    python -m src.ingest --images all         # render all 195 (slow, ~100 MB)
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import pymupdf  # the PDF library: reads text AND renders pages as images

from src import config


# ---------------------------------------------------------------------------
# Step 1: extract the text
# ---------------------------------------------------------------------------

def extract_pages(pdf_path, document_id):
    """
    Read every page of the PDF and return a list of dictionaries:

        [{"document_id": "prospectus", "page": 1, "text": "...",
          "char_count": 4842}, ...]

    The page number is the single most important field in this project. Our
    standing rule is that every answer must cite its page, so we attach the
    number here -- the moment the text comes out of the PDF -- and never let
    go of it.
    """
    pages = []

    # pymupdf.open() gives us the document. Using "with" guarantees the file is
    # closed properly even if something goes wrong halfway through.
    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            # enumerate() counts from 0, but humans and PDF readers count
            # pages from 1. Converting here, once, means every page number
            # downstream is already the one a reviewer would recognise.
            page_number = index + 1

            # "text" mode returns plain reading-order text. PyMuPDF also
            # offers "blocks", "dict" and "html" modes that preserve position
            # information -- we will want those in Month 2 for smarter
            # chunking, but plain text is the right start.
            text = page.get_text("text")

            pages.append({
                "document_id": document_id,
                "page": page_number,
                "text": text,
                "char_count": len(text),
            })

    return pages


# ---------------------------------------------------------------------------
# Step 2: render pages as images
# ---------------------------------------------------------------------------

def parse_page_range(spec, page_count):
    """
    Turn a command-line page selection into an actual list of page numbers.

        "all"       -> [1, 2, 3, ... 195]
        "1-10"      -> [1, 2, ... 10]
        "12,88,91"  -> [12, 88, 91]
        "1-3,88"    -> [1, 2, 3, 88]

    Anything outside the document is dropped rather than crashing, because a
    typo in a page number should not lose you a five-minute extraction run.
    """
    if spec.strip().lower() == "all":
        return list(range(1, page_count + 1))

    wanted = set()

    # Split on commas first: "1-3,88" -> ["1-3", "88"]
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            # A range like "1-10"
            start_text, _, end_text = part.partition("-")
            start, end = int(start_text), int(end_text)
            wanted.update(range(start, end + 1))
        else:
            # A single page like "88"
            wanted.add(int(part))

    # Keep only pages that actually exist, and return them in order.
    return sorted(p for p in wanted if 1 <= p <= page_count)


def render_page_images(pdf_path, document_id, page_numbers, dpi=150):
    """
    Save the chosen pages as PNG image files.

    WHY IMAGES AT ALL?
        A financial statement is a table. Extracted as text, a table becomes a
        soup of numbers with the rows and columns lost. Claude can read a
        picture of the page and see the table as a table. That is Month 6, but
        the images have to exist first.

    WHAT dpi MEANS
        Dots per inch -- how much detail. 150 is a good balance: high enough
        for Claude to read small print in a financial table, low enough that
        files stay a few hundred KB. 72 would be blurry; 300 quadruples the
        file size for little gain.
    """
    written = []

    with pymupdf.open(pdf_path) as doc:
        for page_number in page_numbers:
            # Back to 0-based counting for PyMuPDF's internal index.
            page = doc[page_number - 1]

            # get_pixmap() rasterises the page -- "rasterise" means turning
            # the PDF's drawing instructions into an actual grid of pixels.
            pixmap = page.get_pixmap(dpi=dpi)

            # Zero-padded name so files sort correctly in a file browser:
            # page_009.png comes before page_010.png, but page_9.png does not.
            filename = f"{document_id}_page_{page_number:03d}.png"
            output_path = config.IMAGES_DIR / filename
            pixmap.save(output_path)

            written.append(output_path)

    return written


# ---------------------------------------------------------------------------
# Step 3: save the result
# ---------------------------------------------------------------------------

def save_pages_json(pages, document_id, pdf_path):
    """
    Write everything to one JSON file, wrapped in a small envelope of
    information about the document itself.

    Why an envelope instead of a bare list? Because "which file did this come
    from, and when?" is exactly the question you will ask in four months when
    something looks wrong.
    """
    payload = {
        "document_id": document_id,
        "source_file": pdf_path.name,
        "page_count": len(pages),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
    }

    output_path = config.PAGES_DIR / f"{document_id}.json"

    # ensure_ascii=False keeps Arabic and typographic characters readable in
    # the file instead of turning them into \u escape codes.
    # indent=2 makes it human-inspectable, which matters more than file size.
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return output_path


# ---------------------------------------------------------------------------
# Step 4: report what happened
# ---------------------------------------------------------------------------

def print_summary(pages):
    """
    Print a short health check on the extraction.

    The important number is empty_pages. A page with no text is either
    genuinely blank, or it is a SCANNED IMAGE -- and a scanned page needs OCR,
    which is a Month 9 problem. Better to find out now than in April.
    """
    total_chars = sum(p["char_count"] for p in pages)
    empty_pages = [p["page"] for p in pages if p["char_count"] == 0]
    thin_pages = [p["page"] for p in pages if 0 < p["char_count"] < 100]

    print()
    print(f"  pages extracted : {len(pages)}")
    print(f"  characters      : {total_chars:,}")
    print(f"  average per page: {total_chars // max(len(pages), 1):,}")

    if empty_pages:
        print(f"  EMPTY pages     : {len(empty_pages)} -> {empty_pages[:15]}")
        print("     (no text at all -- these are probably scanned images,")
        print("      which will need OCR later)")
    else:
        print("  empty pages     : none -- the whole document has a text layer")

    if thin_pages:
        print(f"  very thin pages : {len(thin_pages)} -> {thin_pages[:15]}")
        print("     (under 100 characters -- likely section dividers)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # argparse builds a proper command-line interface: it handles --flags,
    # type conversion, and gives you "--help" for free.
    parser = argparse.ArgumentParser(
        description="Extract text and page images from a prospectus PDF."
    )
    parser.add_argument(
        "--pdf",
        default=str(config.PDF_PATH),
        help="path to the PDF (default: prospectus.pdf in the project root)",
    )
    parser.add_argument(
        "--images",
        metavar="PAGES",
        help='render pages as PNG: "all", "1-10", or "12,88,91"',
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="image resolution when rendering (default: 150)",
    )
    args = parser.parse_args()

    # Windows terminals default to an old character set that cannot display
    # the curly apostrophes and Arabic text in this document. This affects
    # printing only -- the extracted data is correct either way.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from pathlib import Path
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"ERROR: no PDF found at {pdf_path}")
        sys.exit(1)

    config.ensure_directories()

    # .stem is the filename without its extension: prospectus.pdf -> prospectus
    document_id = pdf_path.stem

    print(f"Reading {pdf_path.name}  (document_id: {document_id})")

    pages = extract_pages(pdf_path, document_id)
    print_summary(pages)

    output_path = save_pages_json(pages, document_id, pdf_path)
    size_kb = output_path.stat().st_size / 1024
    print()
    print(f"  saved -> {output_path.relative_to(config.PROJECT_ROOT)}  ({size_kb:,.0f} KB)")

    if args.images:
        page_numbers = parse_page_range(args.images, len(pages))
        print()
        print(f"Rendering {len(page_numbers)} page image(s) at {args.dpi} dpi ...")

        written = render_page_images(pdf_path, document_id, page_numbers, dpi=args.dpi)

        total_mb = sum(p.stat().st_size for p in written) / (1024 * 1024)
        print(f"  saved {len(written)} image(s) -> "
              f"{config.IMAGES_DIR.relative_to(config.PROJECT_ROOT)}  "
              f"({total_mb:.1f} MB total)")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
