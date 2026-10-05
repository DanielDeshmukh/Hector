#!/usr/bin/env python3
import os, sys, httpx

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
env_path = os.path.abspath(env_path)
import pytest
if not os.path.exists(env_path):
    pytest.skip("requires local .env with live credentials", allow_module_level=True)
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

key = os.environ["NIM_API_KEY"]
base = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
resp = httpx.post(
    f"{base}/embeddings",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"input": ["murder punishment IPC Section 302"], "model": "nvidia/nv-embedqa-e5-v5", "encoding_format": "float", "input_type": "query"},
    timeout=15,
)
data = resp.json()
vec = data["data"][0]["embedding"]
print("Vector length:", len(vec))

from pinecone import Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
idx = pc.Index("hector-legal")
result = idx.query(vector=vec, top_k=3, include_metadata=True)
matches = result.get("matches", [])
print("Matches:", len(matches))
for m in matches:
    meta = m.get("metadata", {})
    mid = m.get("id", "")
    score = m.get("score", 0)
    act = meta.get("real_act_name", "N/A")
    print(f"  {mid} | score={score:.4f} | act={act}")
