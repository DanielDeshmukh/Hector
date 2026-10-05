"""Live BNS-side retrieval + cross-reference map sanity check.

The passing gates (recall 1.0000 / grounded 0.9944 / fabricated 1.0000) were
measured on gold_iteration1.jsonl, which is 100% IPC (0 of 1185 questions
mention BNS). This checks the side the frontend's IPC-BNS compare view uses.

    python probe_bns_retrieval.py
"""

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ["HECTOR_GOLD_PATH"] = str(EVAL / "gold_iteration1.jsonl")
os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402


def act_of(chunk):
    m = chunk.get("metadata") or {}
    return m.get("act") or m.get("real_act_name") or "?"


def main():
    print("=== cross-reference map ===")
    mp = json.loads((ROOT / "hector" / "api" / "core" / "mapping.json")
                    .read_text(encoding="utf-8"))
    if isinstance(mp, dict):
        print(f"top-level keys: {list(mp)[:8]}  (n={len(mp)})")
        sample_items = list(mp.items())[:3]
        for k, v in sample_items:
            print(f"  {k} -> {v}")
        entries = mp
    else:
        print(f"list of {len(mp)} entries; first 3: {mp[:3]}")
        entries = {str(e.get('old')): e for e in mp if isinstance(e, dict)}

    stack = rge.build_stack()
    ret = stack["retriever"]

    print("\n=== corpus act mix (retriever view) ===")
    print(dict(Counter(a for a in (r.get("act") for r in (ret.records or [])) if a)))

    print("\n=== BNS-side queries (rerank ON, top_k=10, pool=30) ===")
    queries = [
        "What does the Bharatiya Nyaya Sanhita say about murder?",
        "Punishment for theft under BNS section 303",
        "How does BNS define criminal conspiracy?",
        "Section 103 BNS punishment",
        "cheating and dishonesty BNS 318",
    ]
    for q in queries:
        t0 = time.perf_counter()
        chunks = ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
        ms = (time.perf_counter() - t0) * 1000
        acts = Counter(act_of(c) for c in chunks)
        secs = [(c.get("metadata") or {}).get("section_number", "?") for c in chunks[:5]]
        print(f"  {ms:6.0f}ms  {dict(acts)}  top5={secs}")
        print(f"            {q[:64]}")

    print("\n=== IPC vs BNS same-number retrieval (what compare feeds) ===")
    for sec in ("302", "103", "420", "376"):
        for act in ("IPC", "BNS"):
            q = f"Section {sec} {act}"
            chunks = ret.search(q, top_k=5, candidate_pool=30)
            top = chunks[0] if chunks else {}
            m = top.get("metadata") or {}
            print(f"  {q:<22} -> top act={act_of(top):<6} "
                  f"sec={m.get('section_number')} "
                  f"title={str(m.get('section_title'))[:48]}")


if __name__ == "__main__":
    main()
