"""
search_prospectus.py  --  Phase 1 + 3 (learning version)

WHAT THIS DOES
    1. Reads every page of prospectus.pdf and pulls out the text,
       remembering which page each piece of text came from.
    2. Chops each page into small overlapping "passages".
    3. Takes a question you type in plain English, and prints the few
       passages most likely to be relevant -- each labelled with its page.

WHAT THIS DOES *NOT* DO (yet)
    It does not answer your question. It only finds and shows you the
    passages. Nothing here talks to an AI model. That is deliberate:
    in a RAG system this is the "R" (Retrieve) half, and it needs to work
    on its own before we bolt the "G" (Generate) half on top in Phase 4.

HOW TO RUN IT
    python search_prospectus.py "What is the company's main business?"
    python search_prospectus.py            <- will ask you for a question
"""

import re
import sys
import textwrap
from pathlib import Path

from pypdf import PdfReader


# ---------------------------------------------------------------------------
# Settings -- change these numbers and re-run to see what happens.
# ---------------------------------------------------------------------------

# Look for the PDF in the same folder as this script.
PDF_PATH = Path(__file__).parent / "prospectus.pdf"

# How many passages to show you.
HOW_MANY_RESULTS = 5

# How long each passage is, measured in words.
WORDS_PER_PASSAGE = 120

# How far we move along before starting the next passage.
# It is SMALLER than WORDS_PER_PASSAGE on purpose, so passages overlap.
# Without overlap, a sentence that happens to land on a boundary would get
# sliced in half and might not match anything properly.
WORDS_TO_STEP = 60

# Very common English words carry no meaning for searching. If we left "the"
# in, every single passage would match every single question.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "it", "its", "this", "that", "these", "those", "there",
    "what", "which", "who", "whom", "when", "where", "why", "how", "does",
    "do", "did", "has", "have", "had", "can", "could", "will", "would",
    "should", "may", "might", "must", "shall", "about", "into", "than",
    "then", "so", "such", "no", "not", "any", "all", "some", "more", "most",
    "other", "s",
}


# ---------------------------------------------------------------------------
# Step 1: read the PDF, page by page
# ---------------------------------------------------------------------------

def read_pdf_pages(pdf_path):
    """
    Open the PDF and return a list like:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]

    The page number is the single most important thing in this whole file.
    Our project rule is that every answer must cite its page, so we attach
    the page number here -- at the very moment the text is born -- and then
    never let go of it.

    Note: page numbers here start at 1, matching what a human sees in a PDF
    reader. Python lists start at 0, which is why we use start=1 below.
    """
    reader = PdfReader(pdf_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        # extract_text() returns None on a page with no readable text
        # (a full-page image, for example), so we fall back to "".
        text = page.extract_text() or ""
        pages.append({"page": page_number, "text": text})

    return pages


# ---------------------------------------------------------------------------
# Step 2: chop pages into passages
# ---------------------------------------------------------------------------

def split_into_passages(pages):
    """
    Turn a list of pages into a longer list of smaller passages.

    Why bother? A whole page is ~800 words covering several unrelated topics.
    If we showed you a whole page you would still have to hunt through it.
    Smaller passages point at the actual sentence you care about.

    Each passage keeps the page number of the page it was cut from.
    """
    passages = []

    for page in pages:
        # .split() with no arguments splits on ANY whitespace (spaces,
        # newlines, tabs) and throws away the empties. This conveniently
        # cleans up the messy line breaks that PDFs are full of.
        words = page["text"].split()

        # Walk along the page in steps, taking a window of words each time.
        # e.g. words 0-120, then 60-180, then 120-240 ... (they overlap)
        for start in range(0, len(words), WORDS_TO_STEP):
            window = words[start:start + WORDS_PER_PASSAGE]

            # Skip tiny leftovers at the end of a page -- usually just a
            # page number or a footer, never a real answer.
            if len(window) < 25:
                continue

            passages.append({
                "page": page["page"],
                "text": " ".join(window),
            })

    return passages


# ---------------------------------------------------------------------------
# Step 3: score passages against the question
# ---------------------------------------------------------------------------

def extract_keywords(question):
    """
    Turn a plain-English question into the handful of words worth searching for.

        "What is the company's main business?"  ->  {"company", "main", "business"}

    re.findall(r"[a-z']+", ...) grabs runs of letters and apostrophes,
    which drops the "?" and any stray punctuation.
    """
    words = re.findall(r"[a-z']+", question.lower())

    keywords = set()
    for word in words:
        word = word.strip("'")
        if len(word) > 2 and word not in STOPWORDS:
            keywords.add(word)

    return keywords


def score_passage(passage_text, keywords):
    """
    Give a passage a number saying how relevant it looks. Higher is better.

    The scoring has two parts, and the first matters much more:

      1. COVERAGE -- how many DIFFERENT keywords appear at all.
         A passage containing "company" AND "business" is far more likely
         to be what you want than one containing "business" nine times
         and nothing else. Each distinct keyword is worth 10 points.

      2. FREQUENCY -- how many times the keywords appear in total.
         Worth 1 point each. This is only a tie-breaker between passages
         that cover the same keywords.

    Returns the score and which keywords actually matched, so we can show
    you *why* a passage was picked. Being able to see the reason is the
    whole point of starting with keyword search instead of something
    cleverer -- when a result looks wrong, you can find out why.
    """
    lowered = passage_text.lower()

    matched = set()
    total_hits = 0

    for keyword in keywords:
        # r"\b" means "word boundary", so searching for "share" does not
        # secretly match "shareholder" or "sharing".
        hits = len(re.findall(r"\b" + re.escape(keyword) + r"\b", lowered))
        if hits > 0:
            matched.add(keyword)
            total_hits += hits

    score = (len(matched) * 10) + total_hits
    return score, matched


def find_best_passages(passages, question, how_many=HOW_MANY_RESULTS):
    """Score every passage, then hand back the best few."""
    keywords = extract_keywords(question)

    if not keywords:
        return [], keywords

    scored = []
    for passage in passages:
        score, matched = score_passage(passage["text"], keywords)
        if score > 0:                       # ignore passages that matched nothing
            scored.append({
                "score": score,
                "page": passage["page"],
                "text": passage["text"],
                "matched": matched,
            })

    # sort() puts the smallest first, so we sort by NEGATIVE score to get
    # the biggest first.
    scored.sort(key=lambda item: -item["score"])

    return scored[:how_many], keywords


# ---------------------------------------------------------------------------
# Step 4: print it all out nicely
# ---------------------------------------------------------------------------

def print_results(question, keywords, results):
    print()
    print("=" * 78)
    print("QUESTION:", question)
    print("Searching for keywords:", ", ".join(sorted(keywords)) or "(none)")
    print("=" * 78)

    if not results:
        print()
        print("No passages matched. Try different words -- this is a plain")
        print("keyword search, so it can only find words that literally appear")
        print("in the document.")
        return

    for rank, result in enumerate(results, start=1):
        print()
        print(f"--- RESULT {rank}  |  PAGE {result['page']}  |  score {result['score']} ---")
        print(f"    matched: {', '.join(sorted(result['matched']))}")
        print()
        # textwrap stops the passage running off the side of your screen.
        for line in textwrap.wrap(result["text"], width=74):
            print("   ", line)

    print()
    print("=" * 78)
    print("Reminder: these are PASSAGES FROM THE DOCUMENT, not an answer.")
    print("Every one is labelled with the page it came from.")
    print("=" * 78)


# ---------------------------------------------------------------------------
# Main -- this is what runs when you type: python search_prospectus.py
# ---------------------------------------------------------------------------

def main():
    # Windows terminals often default to an old character set called cp1252.
    # The prospectus uses typographic characters like the curly apostrophe in
    # "Group's" (U+2019), which then display as a black diamond. This line
    # switches printing to UTF-8 so they show correctly.
    # Important: this only affects DISPLAY. The text we extracted was always
    # correct -- it was only ever the printing that was wrong.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not PDF_PATH.exists():
        print(f"Could not find the PDF at: {PDF_PATH}")
        sys.exit(1)

    # A question can come from the command line, e.g.
    #     python search_prospectus.py "What is the main business?"
    # sys.argv is the list of things typed after "python". sys.argv[0] is
    # the script name itself, so anything from [1:] onwards is our question.
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Ask a question about the prospectus: ").strip()

    if not question:
        print("No question given -- nothing to search for.")
        sys.exit(1)

    print(f"Reading {PDF_PATH.name} ... (195 pages, this takes a few seconds)")
    pages = read_pdf_pages(PDF_PATH)
    print(f"  read {len(pages)} pages")

    passages = split_into_passages(pages)
    print(f"  cut into {len(passages)} passages")

    results, keywords = find_best_passages(passages, question)
    print_results(question, keywords, results)


# This line means "only run main() if this file was run directly".
# If someone later imports this file to reuse read_pdf_pages(), the search
# will not fire off unexpectedly.
if __name__ == "__main__":
    main()
