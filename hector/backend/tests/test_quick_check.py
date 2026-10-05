#!/usr/bin/env python3
import os, sys
env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
env_path = os.path.abspath(env_path)
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())
sys.path.insert(0, r'D:\Vs Code\VS code\Hector\hector\api')
sys.path.insert(0, r'D:\Vs Code\VS code\Hector\hector')
from data.hybrid_retriever import HectorHybridRetriever
print("Loading retriever...")
r = HectorHybridRetriever()
print("Loaded", len(r.records), "records")
results = r.search("murder punishment IPC", top_k=3)
print("Results:", len(results))
for res in results:
    meta = res.get("metadata", {})
    act = meta.get("real_act_name") or meta.get("act_name") or "N/A"
    score = res.get("score", 0)
    print(f"  {res['id']} | {act} | score={score:.4f}")
