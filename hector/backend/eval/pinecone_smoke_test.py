"""Pinecone connection + retrieval smoke test for the "hector-legal" index.

Settings are taken from the repo's existing setup:
  - index name / embed settings: hector/api/data/hybrid_retriever.py
    (DEFAULT_INDEX_NAME, EMBEDDING_MODEL, EMBEDDING_DIM, _embed_text)
  - env loading: python-dotenv against the repo-root .env

Runs 3 fixed queries with top_k=5. Never prints API keys.
"""

import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]  # <repo root>
API_ROOT = ROOT / "hector" / "api"

load_dotenv(ROOT / ".env")

for _p in (str(API_ROOT), str(ROOT / "hector")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data.hybrid_retriever import (  # noqa: E402
    DEFAULT_INDEX_NAME,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    HectorHybridRetriever,
)
from pinecone import Pinecone  # noqa: E402

INDEX_NAME = DEFAULT_INDEX_NAME  # "hector-legal"
TOP_K = 5
QUERIES = (
    "What is the punishment for murder?",
    "What is the time limit to file a civil suit?",
    "What is the capital of France?",
)


def http_status(exc):
    """Best-effort HTTP status code from an exception (429, 500, ...)."""
    for attr in ("status_code", "status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    if isinstance(value, int):
        return value
    return None


def attempt(label, fn, max_tries=2):
    """Run fn; on error print type/status/message and retry at most once."""
    for try_no in range(1, max_tries + 1):
        try:
            return True, fn()
        except Exception as exc:  # noqa: BLE001
            status = http_status(exc)
            status_txt = f" HTTP status={status}" if status is not None else ""
            print(
                f"[ERROR] {label} (attempt {try_no}/{max_tries}): "
                f"{type(exc).__name__}{status_txt}: {exc}"
            )
    return False, None


def embed_query(text):
    embedder = HectorHybridRetriever.__new__(HectorHybridRetriever)
    vector = embedder._embed_text(text)
    if not vector:
        raise RuntimeError(f"empty embedding returned for query: {text!r}")
    return vector


def show_matches(matches):
    for i, match in enumerate(matches[:TOP_K], 1):
        meta = {}
        if isinstance(match, dict):
            meta = match.get("metadata") or {}
            score = match.get("score")
            match_id = match.get("id")
        else:
            meta = getattr(match, "metadata", None) or {}
            score = getattr(match, "score", None)
            match_id = getattr(match, "id", None)
        act = meta.get("act_name") or meta.get("real_act_name") or meta.get("act")
        section = meta.get("section_number") or meta.get("section") or meta.get("sec")
        page = meta.get("page")
        text = ""
        for key in ("document", "text", "content", "body", "chunk", "page_text"):
            if meta.get(key):
                text = " ".join(str(meta[key]).split())[:120]
                break
        print(f"    [{i}] score={score} id={match_id}")
        print(f"        act={act!r} section={section!r} page={page!r}")
        if text:
            print(f'        text="{text}"')
        else:
            keys = sorted(str(k) for k in meta.keys())
            print(f'        text=<none in metadata> keys={keys}')


def main():
    api_key = os.getenv("PINECONE_API_KEY", "")
    print(f"PINECONE_API_KEY set: {'yes' if api_key else 'no'}")
    if not api_key:
        print("STOP: PINECONE_API_KEY not set.")
        return 1

    print(f"Embedding model (repo): {EMBEDDING_MODEL}")
    print(f"Embedding dim (repo): {EMBEDDING_DIM}")
    print(f"Query embed source: hybrid_retriever._embed_text "
          f"(nvidia/nemotron-3-embed-1b via NIM_BASE_URL, input_type=query)")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(INDEX_NAME)

    def _stats():
        t0 = time.perf_counter()
        stats = index.describe_index_stats()
        return (time.perf_counter() - t0) * 1000.0, stats

    ok, result = attempt("describe_index_stats", _stats)
    if not ok:
        print("Connection: FAILED")
        return 1

    elapsed_ms, stats = result
    if not isinstance(stats, dict):
        stats = stats.to_dict() if hasattr(stats, "to_dict") else dict(stats)
    dimension = stats.get("dimension")
    total = stats.get("total_vector_count")
    namespaces = stats.get("namespaces")
    print("Connection: OK (describe_index_stats succeeded)")
    print(f"Index stats ({INDEX_NAME}): dimension={dimension} "
          f"total_vector_count={total} namespaces={namespaces} "
          f"elapsed_ms={elapsed_ms:.1f}")
    if dimension is not None and dimension != EMBEDDING_DIM:
        print(f"DIMENSION MISMATCH: index={dimension} repo EMBEDDING_DIM={EMBEDDING_DIM}")

    failures = 0
    for query in QUERIES:
        print(f"\n=== QUERY: {query} ===")

        def _embed(q=query):
            return embed_query(q)

        ok, vector = attempt(f"embed: {query}", _embed)
        if not ok:
            failures += 1
            continue
        print(f"  embedding dim={len(vector)} "
              f"(matches index dimension: {'yes' if dimension == len(vector) else 'no'})")

        def _query(vec=vector):
            t0 = time.perf_counter()
            res = index.query(
                vector=vec, top_k=TOP_K, include_metadata=True
            )
            return (time.perf_counter() - t0) * 1000.0, res

        ok, result = attempt(f"query: {query}", _query)
        if not ok:
            failures += 1
            continue
        elapsed_ms, res = result
        if not isinstance(res, dict):
            res = res.to_dict() if hasattr(res, "to_dict") else dict(res)
        matches = res.get("matches") or []
        print(f"  elapsed_ms={elapsed_ms:.1f} matches_returned={len(matches)}")
        show_matches(matches)

    print(f"\nSMOKE TEST DONE (failures={failures})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
