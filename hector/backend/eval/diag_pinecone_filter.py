"""Diagnose why _pinecone_filtered_search returns [] (silent except)."""
import os
import sys
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[3]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from pinecone import Pinecone  # noqa: E402

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
idx = pc.Index("hector")
print("index stats:", idx.describe_index_stats(), flush=True)

flt = {"section_number": {"$eq": "302"}}
print("\n[1] idx.list(filter=..., limit=10) ...", flush=True)
try:
    got = []
    for page in idx.list(filter=flt, limit=10):
        got.extend(v.id for v in page)
    print("  OK ids:", got[:10], flush=True)
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {exc}", flush=True)

print("\n[2] same via retriever._pinecone_filtered_search ...", flush=True)
try:
    from data.hybrid_retriever import HectorHybridRetriever  # noqa: E402
    # minimal instance: reuse class method with a real index, no records
    probe = HectorHybridRetriever.__new__(HectorHybridRetriever)
    probe.pinecone_index = idx
    probe.semantic_disabled = False
    probe.records = []
    probe.collection = None
    out = probe._pinecone_filtered_search(flt, top_k=10)
    print(f"  returned {len(out)} rows", flush=True)
    for row in out[:5]:
        print("   ", row["id"], (row.get("metadata") or {}).get("section_number"),
              flush=True)
except Exception:
    traceback.print_exc()

print("\n[3] filtered VECTOR query (idx.query with filter) ...", flush=True)
try:
    from data.hybrid_retriever import HectorHybridRetriever as H
    probe2 = H.__new__(H)
    probe2.pinecone_index = idx
    probe2.semantic_disabled = False
    emb = probe2._embed_text("Section 302 IPC")
    print(f"  embed dim={len(emb) if emb else None}", flush=True)
    res = idx.query(vector=emb, top_k=10, include_metadata=True, filter=flt)
    matches = res.get("matches", [])
    print(f"  OK {len(matches)} matches", flush=True)
    for m in matches[:5]:
        print("   ", m["id"], m.get("score"),
              (m.get("metadata") or {}).get("section_number"), flush=True)
except Exception:
    traceback.print_exc()
