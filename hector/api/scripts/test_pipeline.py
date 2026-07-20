"""Quick test: embed 10 docs via NIM, upsert to Pinecone, query back."""
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

import httpx
from pinecone import Pinecone

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
NIM_API_KEY = os.getenv("NIM_API_KEY", "")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

pc = Pinecone(api_key=PINECONE_API_KEY)

# 1. Delete old index if exists
existing = [idx.name for idx in pc.list_indexes()]
if "hector-legal" in existing:
    pc.delete_index("hector-legal")
    time.sleep(5)
    print("Deleted old index")

# 2. Create index
pc.create_index(
    name="hector-legal",
    dimension=1024,
    metric="cosine",
    spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
)
time.sleep(10)
print("Created index hector-legal (1024-dim)")

# 3. Embed 10 test docs
test_docs = [
    "Section 302 of BNS deals with murder punishment.",
    "Section 100 of IPC deals with hurt causing death.",
    "Bail provisions under BNSS section 480.",
    "Cruelty by husband under section 498A IPC.",
    "Dowry death punishment under section 304B IPC.",
    "Theft punishment under section 379 IPC.",
    "Cheating under section 420 IPC.",
    "Defamation under section 499 IPC.",
    "Consumer protection act section 12.",
    "Motor vehicles act section 185 drunk driving.",
]

resp = httpx.post(
    f"{NIM_BASE_URL}/embeddings",
    headers={"Authorization": f"Bearer {NIM_API_KEY}", "Content-Type": "application/json"},
    json={"input": test_docs, "model": "nvidia/nv-embedqa-e5-v5", "encoding_format": "float", "input_type": "passage"},
    timeout=30,
)
resp.raise_for_status()
embeddings = [item["embedding"] for item in sorted(resp.json()["data"], key=lambda x: x["index"])]
print(f"Embedded {len(embeddings)} docs (dim={len(embeddings[0])})")

# 4. Upsert
index = pc.Index("hector-legal")
vectors = [
    {"id": f"test-{i}", "values": emb, "metadata": {"document": doc}}
    for i, (doc, emb) in enumerate(zip(test_docs, embeddings))
]
index.upsert(vectors=vectors)
print(f"Upserted {len(vectors)} vectors")

# 5. Query back
query_resp = httpx.post(
    f"{NIM_BASE_URL}/embeddings",
    headers={"Authorization": f"Bearer {NIM_API_KEY}", "Content-Type": "application/json"},
    json={"input": ["What is the punishment for murder?"], "model": "nvidia/nv-embedqa-e5-v5", "encoding_format": "float", "input_type": "query"},
    timeout=30,
)
query_emb = query_resp.json()["data"][0]["embedding"]
results = index.query(vector=query_emb, top_k=3, include_metadata=True)

print("\nQuery: 'What is the punishment for murder?'")
for match in results["matches"]:
    print(f"  {match['id']} score={match['score']:.4f} -> {match['metadata']['document'][:80]}")

print("\nPipeline works! Run migrate_to_pinecone.py for full migration.")
