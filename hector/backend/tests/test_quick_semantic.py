#!/usr/bin/env python3
import os, sys

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
env_path = os.path.abspath(env_path)
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector")

from data.hybrid_retriever import HectorHybridRetriever

r = HectorHybridRetriever.__new__(HectorHybridRetriever)
r.records = []
r.corpus = []
r.tokenized_corpus = []
r.bm25 = None
r.reranker_disabled = True
r.semantic_disabled = False
r._pc = None
r._index = None
r.collection = None
r.cross_encoder = None
r.embed_fn = None

from pinecone import Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
r._pc = pc
r.pinecone_index = pc.Index("hector-legal")

# Check _pinecone property
print("_pinecone:", r._pinecone)
print("_pinecone is None:", r._pinecone is None)
print("semantic_disabled:", r.semantic_disabled)

emb = r._embed_text("murder punishment IPC")
print("Embedding:", emb is not None, len(emb) if emb else 0)

# Direct query
results = r._semantic_search("murder punishment IPC Section 302", top_k=5)
print("Results:", len(results))

# Debug: try the retry wrapper
from utils.retry import retry
query_result = retry(
    r._pinecone.query,
    vector=emb,
    top_k=3,
    include_metadata=True,
    operation_name="pinecone_query",
)
print("Direct query matches:", len(query_result.get("matches", [])))
