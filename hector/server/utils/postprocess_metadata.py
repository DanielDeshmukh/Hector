"""
Post-processing script for HECTOR corpus.
Run after ingestion completes to fix metadata:
1. Add source_type (bare_act / commentary) based on structure_type or filename
2. Backfill section_number from chunk text content
3. Backfill chapter from chunk text content
"""

import re
import sys
import io
try:
    import chromadb
except ImportError:
    chromadb = None
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DB_PATH = "hector_db"
COLLECTION = "indian_law_bns_local"

# --- Patterns for extracting metadata from chunk text ---

# Section number patterns (ordered by specificity)
SECTION_PATTERNS = [
    re.compile(
        r"\[.*?\|\s*Section\s+(\d{1,4}[A-Z]?)\s*\]", re.IGNORECASE
    ),  # [Act | Section N]
    re.compile(
        r"(?:Section|SECTION)\s+(\d{1,4}[A-Z]?)\s*[:\-–]", re.IGNORECASE
    ),  # Section N:
    re.compile(
        r"(?:Section|SECTION)\s+(\d{1,4}[A-Z]?)\.?\s", re.IGNORECASE
    ),  # Section N.
    re.compile(r"(?:^|\n)\s*(\d{1,4}[A-Z]?)\.\s+[^a-z\d]", re.MULTILINE),  # N. Title
]

# Chapter patterns
CHAPTER_PATTERNS = [
    re.compile(r"\[.*?\|\s*(Chapter\s+\w+)", re.IGNORECASE),  # [Act | Chapter X]
    re.compile(r"(?:^|\n)\s*(CHAPTER\s+\w+)\s*[:\s]", re.MULTILINE),  # CHAPTER X
    re.compile(r"(?:^|\n)\s*(PART\s+\w+)\s*[:\s]", re.MULTILINE),  # PART X
]

# Commentary indicators (filenames or content)
COMMENTARY_INDICATORS = [
    "commentary",
    "textbook",
    "ratanlal",
    "monir",
    "durga das",
    "mulla",
    "pollock",
    "merchant of madras",
    "sarkar",
    "viraranjan",
    "bars",
    "halsbury",
    "jolly",
    "advanced",
    "law Lexicon",
    "wharton",
    "z-library",
    "1lib.sk",
    "z-lib.sk",
    "fighting corruption",
]


def extract_section(text):
    """Extract primary section number from chunk text."""
    for pat in SECTION_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return ""


def extract_chapter(text):
    """Extract chapter from chunk text."""
    for pat in CHAPTER_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return ""


def classify_source_type(filename, structure_type, text):
    """Determine if chunk is bare_act or commentary."""
    # Check structure_type first
    if structure_type in ("bare_act", "bare_act_text"):
        return "bare_act"
    if structure_type in ("commentary", "textbook", "legal_commentary"):
        return "commentary"

    # Check filename for commentary indicators
    fname_lower = filename.lower()
    for indicator in COMMENTARY_INDICATORS:
        if indicator.lower() in fname_lower:
            return "commentary"

    # Check content for bare act markers
    first_200 = text[:200].upper()
    if any(
        marker in first_200
        for marker in [
            "AN ACT TO",
            "BE IT ENACTED",
            "SHORT TITLE",
            "CHAPTER I",
            "PART I",
            "PRELIMINARY",
        ]
    ):
        return "bare_act"

    # Check for numbered section pattern (bare act style)
    if re.match(r"^\s*\d+\.\s+[A-Z]", text):
        return "bare_act"

    # Default: if it has numbered sections, treat as bare_act
    if re.search(r"(?:^|\n)\s*\d+\.\s+[A-Z]", text):
        return "bare_act"

    return "commentary"


def main():
    print("=" * 70)
    print("HECTOR POST-PROCESSING: Fix Metadata")
    print("=" * 70)

    client = chromadb.PersistentClient(path=DB_PATH)
    coll = client.get_collection(COLLECTION)
    total = coll.count()
    print(f"\nTotal chunks: {total}")

    # Fetch all chunks
    print("Fetching all chunks...")
    all_data = coll.get(limit=total, include=["documents", "metadatas"])
    ids = all_data["ids"]
    docs = all_data["documents"]
    metas = all_data["metadatas"]

    # Stats
    stats = {
        "source_type_added": 0,
        "section_backfilled": 0,
        "chapter_backfilled": 0,
        "already_ok": 0,
    }
    source_types = Counter()

    print("Processing chunks...")
    for i in range(len(ids)):
        doc = docs[i]
        meta = metas[i]
        changed = False

        # 1. Source type
        current_source_type = meta.get("source_type", "")
        if not current_source_type:
            new_source_type = classify_source_type(
                meta.get("source", ""),
                meta.get("structure_type", ""),
                doc,
            )
            meta["source_type"] = new_source_type
            source_types[new_source_type] += 1
            stats["source_type_added"] += 1
            changed = True
        else:
            source_types[current_source_type] += 1

        # 2. Section number
        current_section = meta.get("section_number", "")
        if not current_section:
            new_section = extract_section(doc)
            if new_section:
                meta["section_number"] = new_section
                stats["section_backfilled"] += 1
                changed = True

        # 3. Chapter
        current_chapter = meta.get("chapter", "")
        if not current_chapter:
            new_chapter = extract_chapter(doc)
            if new_chapter:
                meta["chapter"] = new_chapter
                stats["chapter_backfilled"] += 1
                changed = True

        if not changed:
            stats["already_ok"] += 1

        metas[i] = meta

        if (i + 1) % 5000 == 0:
            print(f"  Processed {i + 1}/{total}...")

    # Write back in batches
    print("\nWriting back to ChromaDB...")
    BATCH = 5000
    for start in range(0, len(ids), BATCH):
        end = min(start + BATCH, len(ids))
        coll.update(ids=ids[start:end], metadatas=metas[start:end])
        print(f"  Batch {start // BATCH + 1}: {end - start} chunks updated")

    # Report
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"  Source types added:     {stats['source_type_added']}")
    print(f"  Sections backfilled:    {stats['section_backfilled']}")
    print(f"  Chapters backfilled:    {stats['chapter_backfilled']}")
    print(f"  Already OK:             {stats['already_ok']}")
    print("\n  Source type distribution:")
    for st, count in source_types.most_common():
        print(f"    {st}: {count}")

    # Verify section coverage
    all_data2 = coll.get(limit=coll.count(), include=["metadatas"])
    with_sec = sum(1 for m in all_data2["metadatas"] if m.get("section_number"))
    with_chap = sum(1 for m in all_data2["metadatas"] if m.get("chapter"))
    with_st = sum(1 for m in all_data2["metadatas"] if m.get("source_type"))
    print("\n  Coverage after post-processing:")
    print(f"    section_number: {with_sec}/{total} ({with_sec * 100 / total:.1f}%)")
    print(f"    chapter:        {with_chap}/{total} ({with_chap * 100 / total:.1f}%)")
    print(f"    source_type:    {with_st}/{total} ({with_st * 100 / total:.1f}%)")
    print("\nDone.")


if __name__ == "__main__":
    main()
