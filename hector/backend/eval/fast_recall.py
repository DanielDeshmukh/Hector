"""fast_recall.py - section_recall@10 without any LLM calls.

section_recall@10 depends only on retrieval, so it can be measured in minutes
instead of the ~12h the full harness needs for generation + judging. This is a
DIAGNOSTIC for fast iteration; the official gate is run_gold_eval.py (hybrid
search + reranker), which also reports citation_grounded_ratio and
fabricated_free_rate.

Mirrors run_gold_eval.section_hit exactly:
  act alias match on document + real_act_name + act_name, then one of the
  section-number regexes over the same haystack.
Denominator = expected sections (items with [] contribute nothing), same as the
harness bump() at run_gold_eval.py:770-777.

Usage:
  python fast_recall.py
  python fast_recall.py --gold gold_set_ipc.jsonl
  python fast_recall.py --limit 100
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GOLD = os.path.join(SCRIPT_DIR, "gold_iteration1.jsonl")
DEFAULT_INDEX = "hector"
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"
TOP_K = 10
WORKERS = 6
EMBED_BATCH = 16

# section_hit / parse_section_spec come straight from the harness so this
# diagnostic can never drift from the official metric.
from run_gold_eval import section_hit  # noqa: E402


def log(m: str) -> None:
    print(f"[fast_recall] {m}", flush=True)


def load_env():
    root = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(root, ".env"))
    except Exception:
        pass
    nim_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    nim_key = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not os.getenv("PINECONE_API_KEY"):
        raise SystemExit("PINECONE_API_KEY missing")
    if not nim_key:
        raise SystemExit("NIM_API_KEY missing")
    return nim_url, nim_key


def embed_many(texts, nim_url, nim_key):
    import httpx

    out, delay = [], 1.0
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        for attempt in range(6):
            try:
                r = httpx.post(
                    f"{nim_url}/embeddings",
                    json={"input": batch, "model": EMBED_MODEL,
                          "encoding_format": "float", "input_type": "query"},
                    headers={"Authorization": f"Bearer {nim_key}"},
                    timeout=90.0,
                )
                if r.status_code in (429, 500, 502, 503, 504):
                    raise RuntimeError(f"http {r.status_code}")
                r.raise_for_status()
                data = sorted(r.json().get("data") or [], key=lambda d: d.get("index", 0))
                out.extend(d["embedding"] for d in data)
                break
            except Exception as exc:
                if attempt == 5:
                    raise
                log(f"embed retry {attempt + 1}: {exc}")
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
        if (i // EMBED_BATCH) % 10 == 0:
            log(f"  embedded {min(i + EMBED_BATCH, len(texts))}/{len(texts)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=DEFAULT_GOLD)
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--topk", type=int, default=TOP_K)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    nim_url, nim_key = load_env()
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    ix = pc.Index(args.index)

    rows = [json.loads(l) for l in open(args.gold, encoding="utf-8") if l.strip()]
    log(f"gold={args.gold} rows={len(rows)} index={args.index} topk={args.topk}")
    if args.limit:
        rows = rows[: args.limit]

    scored = [r for r in rows if r.get("expected_sections")]
    skipped = len(rows) - len(scored)
    log(f"scored={len(scored)} (empty expected_sections: {skipped})")

    # cache query embeddings: re-runs only pay the Pinecone query cost
    import hashlib

    key = hashlib.sha256(f"{os.path.abspath(args.gold)}|{args.index}".encode()).hexdigest()[:16]
    cache_dir = os.path.join(SCRIPT_DIR, "results")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"qvec_{key}.npy")
    vecs = None
    try:
        import numpy as np

        if os.path.exists(cache_path):
            arr = np.load(cache_path, allow_pickle=True)
            if len(arr) == len(scored):
                vecs = [list(map(float, v)) for v in arr]
                log(f"query embedding cache hit: {cache_path} ({len(vecs)} vecs)")
    except Exception as exc:
        log(f"cache load failed ({exc}); re-embedding")
        vecs = None

    if vecs is None:
        t0 = time.time()
        vecs = embed_many([r["question"] for r in scored], nim_url, nim_key)
        log(f"embedded {len(vecs)} queries in {time.time() - t0:.0f}s")
        try:
            import numpy as np

            np.save(cache_path, np.array(vecs, dtype=np.float32))
            log(f"cached -> {cache_path}")
        except Exception as exc:
            log(f"cache save failed ({exc})")

    def query(i_vec):
        i, v = i_vec
        res = ix.query(vector=v, top_k=args.topk, include_metadata=True)
        return i, [m.metadata for m in res["matches"]]

    results = [None] * len(scored)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, mets in pool.map(query, list(enumerate(vecs))):
            results[i] = mets
            done += 1
            if done % 100 == 0:
                log(f"  queried {done}/{len(scored)} in {time.time() - t0:.0f}s")
    log(f"queried {len(scored)} in {time.time() - t0:.0f}s")

    # aggregate exactly like the harness: per expected section, hit if ANY
    # of the top-k chunks matches
    num = den = 0
    per_variant = {}
    per_cat = {}
    misses = []
    for r, mets in zip(scored, results):
        cat = r.get("category", "?")
        var = r.get("variant", "carried")
        for spec in r["expected_sections"]:
            den += 1
            per_cat.setdefault(cat, [0, 0])
            per_cat[cat][1] += 1
            per_variant.setdefault(var, [0, 0])
            per_variant[var][1] += 1
            hit = any(
                section_hit(m.get("document"), m, spec) for m in mets
            )
            if hit:
                num += 1
                per_cat[cat][0] += 1
                per_variant[var][0] += 1
            elif len(misses) < 25:
                misses.append((r["id"], spec, r["question"][:70],
                               [m.get("section_number") for m in mets[:5]]))

    overall = num / den if den else 0.0
    log("=" * 62)
    log(f"DENSE-ONLY section_recall@{args.topk} = {overall:.4f}  ({num}/{den})")
    for v, (k, n) in sorted(per_variant.items()):
        log(f"  variant {v:16} {k / n:.4f}  ({k}/{n})")
    for c, (k, n) in sorted(per_cat.items()):
        log(f"  category {c:20} {k / n:.4f}  ({k}/{n})")
    log(f"gate >=0.98 : {'PASS' if overall >= 0.98 else 'FAIL'}")
    if misses:
        log("sample misses (id, spec, question, top5 sections):")
        for m in misses[:15]:
            log(f"  {m[0]:16} {m[1]:10} {m[2]} -> {m[3]}")
    log("=" * 62)
    return 0 if overall >= 0.98 else 3


if __name__ == "__main__":
    sys.exit(main())
