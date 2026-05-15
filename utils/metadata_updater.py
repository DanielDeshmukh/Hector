
"""
Utility to update existing database records with enhanced legal metadata.

This script enhances existing records by:
1. Inferring act from filename
2. Setting is_bns, is_ipc, is_repealed flags
3. Adding effective dates
4. Marking structure type based on source

For full legal structure extraction, use the enhanced_ingestor to reprocess all PDFs.
"""

import chromadb


DB_PATH = "./hector_db"
COLLECTION_NAME = "indian_law_bns"

# Map filenames to acts (for existing records)
FILENAME_ACT_MAP = {
    "bharatiya nyaya sanhita": "BNS",
    "bharatiya nagarik suraksha sanhita": "BNSS",
    "bharatiya sakshya adhiniyam": "BSA",
    "indian penal code": "IPC",
    "code of criminal procedure": "CRPC",
    "code of criminal": "CRPC",
    "indian evidence act": "IEA",
    "textbook on the bharatiya": "BNS",
    "ratanlal dhirajlal": "IPC",
    "law of evidence": "IEA",
    "whartons law lexicon": "General",
    "the_code_of_criminal": "CRPC",
    "commentary on the narcotic": "NDPS",  # Narcotic Drugs and Psychotropic Substances
    "commentary on the prevention": "PMLA",  # Prevention of Money Laundering
    "commentary on the constitution": "Constitution",
    "p s a pillais": "Hindu Law",
    "principles of statutory interpretation": "Legal Reference",
    "s krishnamurthi aiyar": "Hindu Law",
}


def infer_act_from_source(source: str) -> dict:
    """Infer act and related metadata from source filename."""
    # Normalize: replace underscores with spaces for matching
    source_normalized = source.lower().replace("_", " ")

    for key, act in FILENAME_ACT_MAP.items():
        if key in source_normalized:
            result = {
                "act_name": act,
                "structure_type": "bare_act" if act in ["BNS", "BNSS", "BSA", "IPC", "CRPC", "IEA", "CPC"] else "commentary"
            }

            # Set legal flags
            if act == "BNS":
                result.update({
                    "is_bns": True,
                    "is_repealed": False,
                    "effective_date": "2024-07-01"
                })
            elif act == "BNSS":
                result.update({
                    "is_bnss": True,
                    "is_repealed": False,
                    "effective_date": "2024-07-01"
                })
            elif act == "BSA":
                result.update({
                    "is_bsa": True,
                    "is_repealed": False,
                    "effective_date": "2024-07-01"
                })
            elif act == "IPC":
                result.update({
                    "is_ipc": True,
                    "is_repealed": True,
                    "effective_date": "1860-01-01",
                    "replaced_by": "BNS (w.e.f. 2024-07-01)"
                })
            elif act == "CRPC":
                result.update({
                    "is_crpc": True,
                    "is_repealed": True,
                    "effective_date": "1973-01-01",
                    "replaced_by": "BNSS (w.e.f. 2024-07-01)"
                })
            else:
                result["is_repealed"] = False

            return result

    return {"act_name": "Unknown", "structure_type": "general_legal_text"}


def update_metadata():
    """Update all records in the database with enhanced metadata."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_count = collection.count()
    print(f"Current record count: {total_count}")

    # Get all records using peek (returns all in memory)
    results = collection.peek(limit=total_count)

    if not results.get("ids"):
        print("No records found!")
        return

    print(f"Processing {len(results['ids'])} records...")

    # Process in batches
    batch_size = 500
    total = len(results["ids"])

    for i in range(0, total, batch_size):
        batch_ids = []
        batch_metadatas = []

        for j in range(i, min(i + batch_size, total)):
            original_metadata = dict(results["metadatas"][j])
            source = original_metadata.get("source", "")

            # Get enhanced metadata
            enhanced = infer_act_from_source(source)

            # Merge: keep original + add enhanced
            updated = {**original_metadata, **enhanced}
            updated["mapping_accuracy"] = "enhanced_v1"

            batch_ids.append(results["ids"][j])
            batch_metadatas.append(updated)

        # Update batch
        collection.update(ids=batch_ids, metadatas=batch_metadatas)

        print(f"  Updated {min(i + batch_size, total)}/{total} records...")

    print(f"\n[*] Metadata update complete!")
    print(f"  Total records: {collection.count()}")

    # Show sample
    sample = collection.peek(limit=1)
    if sample.get("metadatas"):
        print(f"\nSample metadata keys: {list(sample['metadatas'][0].keys())}")


if __name__ == "__main__":
    update_metadata()