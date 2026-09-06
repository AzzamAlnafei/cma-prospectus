"""
search.py -- keyword search over the chunk library.

WHAT THIS IS FOR
    Two things:

    1. Something you can actually RUN today, to see Phase 2's output working.
       Ask a question, get passages back with real citations.

    2. The BASELINE. Phase 3 replaces this scoring with embeddings, which match
       meaning instead of letters. To claim that embeddings are better you have
       to know what "better" is better THAN -- and this is that number.

WHAT IT IS NOT
    This is not the retrieval system. Keyword search matches letters, so asking
    "what is the main business" cannot find "the Bank provides retail and
    corporate banking services" -- not one word overlaps. That limit is called
    VOCABULARY MISMATCH and it is the reason Phase 3 exists.

    It does not disappear, though. In Phase 4 this scoring becomes the keyword
    half of hybrid search, because prospectuses are full of exact terms --
    defined terms, SAR figures, section numbers -- where literal matching
    genuinely beats meaning-matching. It is a component, never the architecture.

HOW TO RUN IT
    python -m src.search "What are the risks related to liquidity?"
    python -m src.search "capital adequacy" --market sukuk
    python -m src.search "use of proceeds" --top 3
    python -m src.search                       # will ask you for a question
"""

import argparse
import json
import re
import sys
import textwrap

# ---------------------------------------------------------------------------
# Let this file be run BOTH ways:
#     python -m src.search          <- the normal way
#     python src/search.py          <- e.g. the Run button in VS Code
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

from src import chunks as chunking
from src import config


# Very common words carry no meaning for searching. Leaving "the" in would make
# every chunk match every question.
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


def load_chunks(market=None, document_id=None):
    """
    Read the chunk files produced by `python -m src.ingest`.

    Returns a flat list of chunks across the whole library, optionally filtered
    to one market or one document. Because every chunk already carries its
    document_id and market, filtering is just a list comprehension -- no
    special "which file am I searching" logic anywhere.
    """
    all_chunks = []

    for path in sorted(config.CHUNKS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)

        if market and payload["market"] != market:
            continue
        if document_id and payload["document_id"] != document_id:
            continue

        all_chunks.extend(payload["chunks"])

    return all_chunks


def extract_keywords(question):
    """
    Turn a plain-English question into the words worth searching for.

        "What are the risks related to liquidity?" -> {"risks", "related", "liquidity"}
    """
    words = re.findall(r"[a-z']+", question.lower())

    keywords = set()
    for word in words:
        word = word.strip("'")
        if len(word) > 2 and word not in STOPWORDS:
            keywords.add(word)

    return keywords


def score_chunk(text, keywords):
    """
    Score one chunk. Higher is better.

    Two parts, and the first matters far more:

      COVERAGE  -- how many DIFFERENT keywords appear at all. A chunk with
                   "liquidity" AND "risks" is much more likely to be what you
                   want than one with "risks" nine times and nothing else.
                   Worth 10 points each.
      FREQUENCY -- total occurrences, worth 1 point each. A tie-breaker only.

    Also returns which keywords matched, so the output can show you WHY a chunk
    was chosen. Being able to see the reason is the whole point of starting
    with something this simple.
    """
    lowered = text.lower()

    matched = set()
    total_hits = 0

    for keyword in keywords:
        # \b is a word boundary, so "share" does not secretly match
        # "shareholder" or "sharing".
        hits = len(re.findall(r"\b" + re.escape(keyword) + r"\b", lowered))
        if hits:
            matched.add(keyword)
            total_hits += hits

    return (len(matched) * 10) + total_hits, matched


def search(chunks, question, top_k=5):
    """Score every chunk and return the best few, with the keywords used."""
    keywords = extract_keywords(question)
    if not keywords:
        return [], keywords

    scored = []
    for chunk in chunks:
        score, matched = score_chunk(chunk["text"], keywords)
        if score > 0:
            scored.append({**chunk, "score": score, "matched": matched})

    # sort() puts smallest first, so sort by NEGATIVE score for biggest first.
    scored.sort(key=lambda c: -c["score"])
    return scored[:top_k], keywords


def print_results(question, keywords, results, searched_count):
    print()
    print("=" * 78)
    print("QUESTION:", question)
    print("Keywords :", ", ".join(sorted(keywords)) or "(none)")
    print(f"Searched : {searched_count:,} chunks")
    print("=" * 78)

    if not results:
        print()
        print("Nothing matched. This is plain keyword search -- it can only find")
        print("words that literally appear in the document. Phase 3 fixes that.")
        return

    for rank, chunk in enumerate(results, start=1):
        print()
        print(f"--- {rank}  [{chunk['market']}]  {chunking.citation_for(chunk)}"
              f"   (score {chunk['score']})")
        if chunk["section_path"]:
            print(f"    {chunk['section_path'][:74]}")
        print(f"    matched: {', '.join(sorted(chunk['matched']))}")
        print()
        for line in textwrap.wrap(chunk["text"], width=74):
            print("   ", line)

    print()
    print("=" * 78)
    print("These are PASSAGES FROM THE DOCUMENTS, not answers. Answering with")
    print("citations is Phase 5.")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="Keyword search over the ingested prospectus library."
    )
    parser.add_argument("question", nargs="*", help="what to search for")
    parser.add_argument("--market", choices=config.MARKETS,
                        help="search one market only")
    parser.add_argument("--document", help="search one document_id only")
    parser.add_argument("--top", type=int, default=5,
                        help="how many passages to show (default: 5)")
    args = parser.parse_args()

    # Windows terminals default to an old character set that cannot print the
    # curly apostrophes in these documents. Display only -- the data is fine.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    chunks = load_chunks(market=args.market, document_id=args.document)

    if not chunks:
        print("No chunks found. Run this first:")
        print("    python -m src.ingest")
        sys.exit(1)

    question = " ".join(args.question) or input("Ask a question: ").strip()
    if not question:
        print("No question given.")
        sys.exit(1)

    results, keywords = search(chunks, question, top_k=args.top)
    print_results(question, keywords, results, len(chunks))


if __name__ == "__main__":
    main()
