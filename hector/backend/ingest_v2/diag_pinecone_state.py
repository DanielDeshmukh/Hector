"""Verify the new Pinecone credential and report index names/dimensions.

Prints index NAME, DIMENSION, HOST, METRIC and vector count only - never the
API key value (only whether it was found and its length).
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../Hector


def load_env(name):
    p = ROOT / ".env"
    if not p.exists():
        return os.environ.get(name, "")
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    return os.environ.get(name, "")


key = load_env("PINECONE_API_KEY")
print(f"PINECONE_API_KEY found={bool(key)} len={len(key)}")
if not key:
    raise SystemExit("no key")

from pinecone import Pinecone  # noqa: E402

pc = Pinecone(api_key=key)
rows = []
for idx in pc.list_indexes():
    name = idx.name
    info = pc.describe_index(name)
    rows.append({
        "name": name,
        "dim": getattr(info, "dimension", None),
        "host": getattr(info, "host", None),
        "metric": getattr(getattr(info, "metric", None), "value", None)
                  or getattr(info, "metric", None),
        "vectors": (info.total_vector_count
                    if hasattr(info, "total_vector_count") else None),
    })
print(f"\nindexes on this key: {len(rows)}")
for r in sorted(rows, key=lambda x: x["name"]):
    print(f"  name={r['name']!r} dim={r['dim']} metric={r['metric']} "
          f"vectors={r['vectors']} host={r['host']}")

wanted = "hector-legal-v2"
print(f"\n{wanted!r} present: {wanted in {r['name'] for r in rows}}")
