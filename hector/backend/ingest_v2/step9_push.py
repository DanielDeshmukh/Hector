"""step9_push.py - embed output/eval_corpus.jsonl and upsert to hector-legal-v2.

Builds the NEW production index from the id-stable corpus made by step8_corpus.py
so that the Pinecone dense leg and the eval BM25 leg share one id space (RRF
fusion joins by id) and one text source (metadata.document).

Embedding matches how the rest of the stack embeds for Pinecone
(api/scripts/reingest_full.py:183-206, migrate_to_pinecone.py:119-137):
    POST {NIM_BASE_URL}/embeddings  model=nvidia/nemotron-3-embed-1b
    input_type=passage, truncate=END   -> 2048 dims, cosine

Usage:
  python step9_push.py --limit 64        # smoke test (recommended first)
  python step9_push.py                   # full upsert
  python step9_push.py --reset           # delete all vectors first, then full
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HERE, "output", "eval_corpus.jsonl")
INDEX_NAME = "hector"
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"
DIM = 2048
EMBED_BATCH = 16
UPSERT_BATCH = 64
WORKERS = 4
SEED = 20261013


def log(msg: str) -> None:
    print(f"[step9] {msg}", flush=True)


def load_env():
    root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(root, ".env"))
    except Exception:
        pass
    key = os.getenv("PINECONE_API_KEY")
    if not key:
        raise SystemExit("PINECONE_API_KEY missing")
    nim_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    nim_key = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not nim_key:
        raise SystemExit("NIM_API_KEY missing")
    return key, nim_url, nim_key


def embed_batch(texts: list[str], nim_url: str, nim_key: str) -> list[list[float]]:
    import httpx

    payload = {
        "input": texts,
        "model": EMBED_MODEL,
        "encoding_format": "float",
        "input_type": "passage",
        "truncate": "END",
    }
    delay = 1.0
    for attempt in range(6):
        try:
            r = httpx.post(
                f"{nim_url}/embeddings",
                json=payload,
                headers={"Authorization": f"Bearer {nim_key}"},
                timeout=120.0,
            )
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"http {r.status_code}: {r.text[:160]}")
            r.raise_for_status()
            data = r.json().get("data") or []
            # NIM returns results ordered by index; enforce it
            data = sorted(data, key=lambda d: d.get("index", 0))
            vecs = [d["embedding"] for d in data]
            for v in vecs:
                if len(v) != DIM:
                    raise RuntimeError(f"dim {len(v)} != {DIM}")
            if len(vecs) != len(texts):
                raise RuntimeError(f"got {len(vecs)} vectors for {len(texts)} inputs")
            return vecs
        except Exception as exc:
            if attempt == 5:
                raise
            log(f"embed retry {attempt + 1}: {type(exc).__name__}: {exc}")
            time.sleep(delay)
            delay = min(delay * 2, 30.0)
    raise RuntimeError("unreachable")


def read_corpus(path: str, limit: int, acts: set[str] | None = None) -> list[dict]:
    if not os.path.isfile(path):
        raise SystemExit(f"missing corpus: {path} (run step8_corpus.py first)")
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if acts and row.get("metadata", {}).get("act_id") not in acts:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


_SCALAR = (str, int, float, bool)


def sanitize_metadata(meta: dict) -> dict:
    """Pinecone only accepts str/number/bool/list[str] - no nulls, no nesting.

    v2 records legitimately carry nulls (e.g. repealed_on/replaced_by are null
    on the 21 `omitted` sections), so drop them here at the storage boundary
    rather than falsifying them in the jsonl artifact.
    """
    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, _SCALAR):
            out[k] = v
        elif isinstance(v, list) and all(isinstance(x, str) for x in v):
            out[k] = v
        elif isinstance(v, (dict, tuple, set)):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = str(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only push first N (smoke test)")
    ap.add_argument("--acts", type=str, default="", help="comma-separated act_ids to push (e.g. bnss-2023,bsa-2023); empty = all")
    ap.add_argument("--reset", action="store_true", help="delete all vectors first")
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    api_key, nim_url, nim_key = load_env()
    act_filter = {a.strip() for a in args.acts.split(",") if a.strip()} or None
    rows = read_corpus(CORPUS_PATH, args.limit, act_filter)
    log(f"seed={SEED} corpus={CORPUS_PATH} rows={len(rows)}"
        + (f" acts={sorted(act_filter)}" if act_filter else ""))
    log(f"index={INDEX_NAME} model={EMBED_MODEL} dim={DIM}")

    from pinecone import Pinecone

    pc = Pinecone(api_key=api_key)
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        raise SystemExit(f"index {INDEX_NAME} not found")
    ix = pc.Index(INDEX_NAME)

    before = ix.describe_index_stats().total_vector_count
    log(f"index vectors before: {before}")
    if args.reset:
        if args.limit:
            raise SystemExit("--reset cannot be combined with --limit")
        ix.delete(delete_all=True, namespace="")
        time.sleep(3)
        log(f"index vectors after reset: "
            f"{ix.describe_index_stats().total_vector_count}")

    t0 = time.time()
    done = 0
    failed = 0

    def work(chunk: list[dict]) -> int:
        texts = [r["document"] for r in chunk]
        vecs = embed_batch(texts, nim_url, nim_key)
        upserts = []
        for r, v in zip(chunk, vecs):
            meta = sanitize_metadata(r["metadata"])
            doc = r["document"]
            # Pinecone caps metadata at 40960 bytes/vector; BNSS s531
            # (repeal+savings) alone is 195KB. Truncate at the storage
            # boundary like sanitize_metadata does for nulls - the jsonl
            # keeps the full text for BM25/eval.
            if len(doc.encode("utf-8")) > 36000:
                cut = doc[:30000]
                doc = cut + "\n…[truncated for index metadata]"
                log(f"truncated {r['id']} document to {len(doc)} chars")
            meta["document"] = doc  # dense leg reads this
            upserts.append({"id": r["id"], "values": v, "metadata": meta})
        ix.upsert(vectors=upserts, namespace="")
        return len(upserts)

    chunks = [rows[i:i + EMBED_BATCH] for i in range(0, len(rows), EMBED_BATCH)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, result in enumerate(pool.map(work, chunks), 1):
            done += result
            if n % 25 == 0 or n == len(chunks):
                el = time.time() - t0
                rate = done / el if el else 0
                eta = (len(rows) - done) / rate if rate else 0
                log(f"  {n}/{len(chunks)} batches | {done} vectors | "
                    f"{el:.0f}s | {rate:.0f}/s | eta {eta:.0f}s")

    after = ix.describe_index_stats().total_vector_count
    stats = {
        "seed": SEED,
        "index": INDEX_NAME,
        "pushed": done,
        "failed": failed,
        "index_before": before,
        "index_after": after,
        "elapsed_s": round(time.time() - t0, 1),
        "limit": args.limit,
        "reset": args.reset,
    }
    log("STATS " + json.dumps(stats))
    if failed:
        log(f"FAIL: {failed} chunks failed")
        return 3
    log("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
