"""Sanity-check the freshly populated `hector` index: vector count, then one
dense query per act to confirm both IPC and BNS sections are retrievable
using the same embed model the API uses (nemotron-3-embed-1b, query-side).

Prints ids/metadata only, never keys.
"""

import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]


def env(name):
    p = ROOT / ".env"
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, v = s.partition("=")
            if k.strip() == name:
                return v.strip().strip('"').strip("'")
    return os.environ.get(name, "")


key = env("PINECONE_API_KEY")
nim_key = env("NIM_API_KEY")
nim_url = env("NIM_BASE_URL") or "https://integrate.api.nvidia.com/v1"
INDEX = os.getenv("HECTOR_EVAL_INDEX", "hector")

from pinecone import Pinecone  # noqa: E402

pc = Pinecone(api_key=key)
ix = pc.Index(INDEX)
stats = ix.describe_index_stats()
print(f"index={INDEX} total_vector_count={stats.total_vector_count}")

EMBED_MODEL = "nvidia/nemotron-3-embed-1b"


def embed(text):
    with httpx.Client(timeout=30) as c:
        r = c.post(
            f"{nim_url}/embeddings",
            headers={"Authorization": f"Bearer {nim_key}",
                     "Content-Type": "application/json"},
            json={"input": [text], "model": EMBED_MODEL,
                  "encoding_format": "float", "input_type": "query"},
        )
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]


QUERIES = [
    ("IPC", "punishment for murder under the Indian Penal Code"),
    ("BNS", "punishment for murder under the Bharatiya Nyaya Sanhita"),
]

for act, q in QUERIES:
    v = embed(q)
    res = ix.query(vector=v, top_k=5, include_metadata=True)
    m = res.get("matches") or []
    print(f"\n{act}: {q!r} -> {len(m)} matches")
    for x in m[:5]:
        md = x.get("metadata") or {}
        print(f"   {x['score']:.4f} {x['id']:<26} act={md.get('act')!r} "
              f"section={md.get('section_number')!r} "
              f"title={str(md.get('section_title'))[:52]!r}")
