"""precompute_embs.py - embed output/eval_corpus.jsonl once and save an npz.

Produces output/eval_corpus_embs.npz {ids, matrix, model, dim} with the same
embed path step9_push.py used for the Pinecone index (nvidia/nemotron-3-embed-1b,
2048 dims, input_type=passage) so the API's local dense fallback can cosine-match
queries offline while Pinecone reads are paused.

Usage:
  python precompute_embs.py              # full embed
  python precompute_embs.py --limit 32   # smoke test
  python precompute_embs.py --out x.npz
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HERE, "output", "eval_corpus.jsonl")
OUT_PATH = os.path.join(HERE, "output", "eval_corpus_embs.npz")
EMBED_BATCH = 16
WORKERS = 4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from step9_push import EMBED_MODEL, DIM, embed_batch, read_corpus


def log(msg: str) -> None:
    print(f"[precompute] {msg}", flush=True)


def load_env():
    root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(root, ".env"))
    except Exception:
        pass
    nim_url = os.getenv(
        "NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
    ).rstrip("/")
    nim_key = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not nim_key:
        raise SystemExit("NIM_API_KEY missing")
    return nim_url, nim_key


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only embed first N")
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args()

    nim_url, nim_key = load_env()
    rows = read_corpus(CORPUS_PATH, args.limit)
    ids = [r["id"] for r in rows]
    texts = [r["document"] for r in rows]
    log(f"corpus={CORPUS_PATH} rows={len(rows)}")
    log(f"model={EMBED_MODEL} dim={DIM} out={args.out}")

    chunks = [
        list(range(i, min(i + EMBED_BATCH, len(texts))))
        for i in range(0, len(texts), EMBED_BATCH)
    ]
    vecs: list[list[float] | None] = [None] * len(texts)
    t0 = time.time()

    def work(idx: list[int]) -> int:
        out = embed_batch([texts[i] for i in idx], nim_url, nim_key)
        for i, v in zip(idx, out):
            vecs[i] = v
        return len(idx)

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, result in enumerate(pool.map(work, chunks), 1):
            done += result
            if n % 10 == 0 or n == len(chunks):
                el = time.time() - t0
                log(f"  {n}/{len(chunks)} batches | {done} vectors | {el:.0f}s")

    import numpy as np

    matrix = np.asarray(vecs, dtype=np.float16)
    if matrix.shape != (len(rows), DIM):
        raise SystemExit(f"bad matrix shape {matrix.shape} != ({len(rows)}, {DIM})")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    np.savez_compressed(
        args.out,
        ids=np.asarray(ids),
        matrix=matrix,
        model=np.asarray(EMBED_MODEL),
        dim=np.asarray(DIM),
    )
    size = os.path.getsize(args.out)
    log(f"saved shape={matrix.shape} bytes={size} ({size / 1e6:.1f} MB)")
    log("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
