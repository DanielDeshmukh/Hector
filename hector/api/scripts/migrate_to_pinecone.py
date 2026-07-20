"""
Migrate local ChromaDB data to Pinecone Cloud.
Uses NVIDIA NIM API for embeddings (user already has API key).

Usage:
    python api/scripts/migrate_to_pinecone.py

Reads all records from local hector_db ChromaDB, embeds via NIM,
and upserts to Pinecone index.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
NIM_API_KEY = os.getenv("NIM_API_KEY", "")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
INDEX_NAME = "hector-legal"
DIMENSION = 1024
EMBEDDING_MODEL = "nvidia/nv-embedqa-e5-v5"
BATCH_SIZE = 100
EMBED_BATCH_SIZE = 50
PROGRESS_FILE = "pinecone_migration_progress.json"


def get_local_records():
    """Read all records from local ChromaDB."""
    try:
        import chromadb
    except ImportError:
        print("ERROR: chromadb not installed.")
        sys.exit(1)

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "..", "hector_db",
    )
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        print(f"ERROR: Local database not found at {db_path}")
        sys.exit(1)

    print(f"Reading from: {db_path}")
    client = chromadb.PersistentClient(path=db_path)
    collections = client.list_collections()

    collection = None
    for c in collections:
        if "indian_law_bns" in c.name:
            collection = client.get_collection(c.name)
            print(f"Collection: {c.name} ({collection.count()} records)")
            break

    if collection is None:
        print("ERROR: No matching collection found.")
        sys.exit(1)

    records = []
    batch_size = 5000
    offset = 0
    total = collection.count()

    while offset < total:
        batch = collection.get(
            include=["documents", "metadatas"],
            limit=batch_size,
            offset=offset,
        )
        docs = batch.get("documents") or []
        metas = batch.get("metadatas") or []
        ids = batch.get("ids") or []

        for i, doc in enumerate(docs):
            meta = dict(metas[i]) if i < len(metas) else {}
            records.append({
                "id": ids[i] if i < len(ids) else f"rec-{offset+i}",
                "document": doc,
                "metadata": meta,
            })
        offset += batch_size
        print(f"  Loaded {min(offset, total)}/{total}...")

    return records


def embed_with_nim(texts):
    """Embed texts using NVIDIA NIM API."""
    import httpx

    all_embeddings = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        for attempt in range(5):
            try:
                resp = httpx.post(
                    f"{NIM_BASE_URL}/embeddings",
                    headers={
                        "Authorization": f"Bearer {NIM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": batch,
                        "model": EMBEDDING_MODEL,
                        "encoding_format": "float",
                        "input_type": "passage",
                    },
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                for item in sorted(data.get("data", []), key=lambda x: x["index"]):
                    all_embeddings.append(item["embedding"])
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    wait = 10 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  Error on batch {i}: {e}")
                    time.sleep(5)

        done = min(i + EMBED_BATCH_SIZE, len(texts))
        if done % (EMBED_BATCH_SIZE * 5) == 0 or done == len(texts):
            print(f"  Embedded {done}/{len(texts)}...")

        time.sleep(1)

    return all_embeddings


def upsert_to_pinecone(records, embeddings):
    """Upsert records to Pinecone index."""
    from pinecone import Pinecone

    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating index: {INDEX_NAME} (dim={DIMENSION})")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
        )
        time.sleep(10)

    index = pc.Index(INDEX_NAME)
    total = len(records)
    for i in range(0, total, BATCH_SIZE):
        batch_records = records[i : i + BATCH_SIZE]
        batch_embeddings = embeddings[i : i + BATCH_SIZE]

        vectors = []
        for rec, emb in zip(batch_records, batch_embeddings):
            meta = dict(rec["metadata"])
            meta["document"] = rec["document"]
            vectors.append({
                "id": rec["id"],
                "values": emb,
                "metadata": meta,
            })

        index.upsert(vectors=vectors)
        if (i + BATCH_SIZE) % (BATCH_SIZE * 10) == 0 or i + BATCH_SIZE >= total:
            print(f"  Upserted {min(i + BATCH_SIZE, total)}/{total}...")

    stats = index.describe_index_stats()
    print(f"\nDone! Total vectors: {stats.get('total_vector_count', '?')}")


def main():
    if not PINECONE_API_KEY:
        print("ERROR: PINECONE_API_KEY not set")
        sys.exit(1)
    if not NIM_API_KEY:
        print("ERROR: NIM_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("HECTOR: ChromaDB -> Pinecone Migration")
    print("=" * 60)

    records = get_local_records()
    texts = [r["document"] for r in records]

    print(f"\nEmbedding {len(texts)} docs via NVIDIA NIM API...")
    embeddings = embed_with_nim(texts)

    if len(embeddings) != len(records):
        print(f"ERROR: Embedding count mismatch ({len(embeddings)} vs {len(records)})")
        sys.exit(1)

    print(f"\nUpserting {len(records)} vectors to Pinecone...")
    upsert_to_pinecone(records, embeddings)

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
