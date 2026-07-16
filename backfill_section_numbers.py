"""Backfill section_number metadata from document text for chunks missing it."""
import os, re, sys
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, r"D:\Vs Code\VS code\Hector")
import chromadb

SECTION_PATTERNS = [
    re.compile(r"\[s\s*(\d{1,4}[a-z]?)\]", re.IGNORECASE),
    re.compile(r"\[Section\s+(\d{1,4}[a-z]?)\]", re.IGNORECASE),
    re.compile(r"(?:^|\n)\s*(\d{1,4}[a-z]?)\.\s", re.MULTILINE),
    re.compile(r"(?:^|\n)(?:Section|sec\.?|s\.)\s+(\d{1,4}[a-z]?)", re.IGNORECASE | re.MULTILINE),
]

def extract_section_from_text(doc_text):
    for pattern in SECTION_PATTERNS:
        match = pattern.search(doc_text)
        if match:
            return match.group(1).lower()
    return None

c = chromadb.PersistentClient(path=r"D:\Vs Code\VS code\Hector\hector_db")
col = c.get_collection("indian_law_bns_local")

print("Scanning all chunks for missing section_number...")
BATCH = 5000
offset = 0
updated = 0
already_has = 0
no_section_found = 0
total = 0

while True:
    results = col.get(limit=BATCH, offset=offset, include=["metadatas", "documents"])
    docs = results["documents"]
    metas = results["metadatas"]
    ids = results["ids"]
    if not docs:
        break

    to_update_ids = []
    to_update_metas = []

    for i in range(len(docs)):
        total += 1
        meta = metas[i]
        if meta.get("section_number"):
            already_has += 1
            continue

        section = extract_section_from_text(docs[i])
        if section:
            new_meta = dict(meta)
            new_meta["section_number"] = section
            to_update_ids.append(ids[i])
            to_update_metas.append(new_meta)
            updated += 1
        else:
            no_section_found += 1

    if to_update_ids:
        for j in range(0, len(to_update_ids), 1000):
            batch_ids = to_update_ids[j:j+1000]
            batch_metas = to_update_metas[j:j+1000]
            col.update(ids=batch_ids, metadatas=batch_metas)

    offset += BATCH
    print(f"  Processed {total} chunks, updated {updated}, no section found {no_section_found}")

print(f"\n=== DONE ===")
print(f"Total chunks: {total}")
print(f"Already had section_number: {already_has}")
print(f"Updated with extracted section: {updated}")
print(f"No section found in text: {no_section_found}")
