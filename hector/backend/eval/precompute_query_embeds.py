"""precompute_query_embeds.py - batch NIM query embeddings for the retrieval gate.

search() embeds the (possibly expanded) query through one NIM POST per call
(hybrid_retriever._embed_text -> _matrix_dense_search:1617), costing ~1-6s per
question and dominating sweep runtime. This script performs the identical call
once for every gold question's raw and expanded text - same model
(nvidia/nemotron-3-embed-1b), same input_type=query, same truncate=END - and
stores sha1(text) -> 2048d vector in query_embeds.npz. sweep_retrieval_gate.py
then serves vectors from that file and never touches the embed API.

Resumable: texts already present (by sha1) are skipped; the npz is saved after
every batch. Chunked: --offset/--limit slice the gold rows BEFORE text
collection, so each invocation stays under ~15 min.

Usage:
  python precompute_query_embeds.py --act bsa                 # one act
  python precompute_query_embeds.py --act ipc --offset 600 --limit 562
  python precompute_query_embeds.py --all                     # everything left
  python precompute_query_embeds.py --status                  # counts only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "api")))

os.environ.setdefault("HF_HUB_OFFLINE", "1")

for _line in open(os.path.join(SCRIPT_DIR, "..", "..", "..", ".env"), encoding="utf-8"):
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k, _v)

from run_gold_eval import read_jsonl  # noqa: E402

GOLD = {
    "ipc": os.path.join(SCRIPT_DIR, "gold_set_ipc.jsonl"),
    "bns": os.path.join(SCRIPT_DIR, "gold_bns.jsonl"),
    "bnss": os.path.join(SCRIPT_DIR, "gold_bnss.jsonl"),
    "bsa": os.path.join(SCRIPT_DIR, "gold_bsa.jsonl"),
    "iea": os.path.join(SCRIPT_DIR, "gold_iea.jsonl"),
    "crpc": os.path.join(SCRIPT_DIR, "gold_crpc.jsonl"),
}
EMBED_CACHE = os.path.join(SCRIPT_DIR, "query_embeds.npz")
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"  # hybrid_retriever.EMBED_NIM_MODEL
DIM = 2048
BATCH = 16

_expander = None


def log(msg: str) -> None:
    print(f"[preq] {msg}", flush=True)


def get_expander():
    global _expander
    if _expander is None:
        from core.query_expander import QueryExpander

        _expander = QueryExpander()
    return _expander


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_cache() -> tuple[dict[str, int], list[str], object]:
    """Return ({sha1: row index}, [sha1 keys], vecs array-or-empty)."""
    import numpy as np

    if not os.path.exists(EMBED_CACHE):
        return {}, [], np.empty((0, DIM), dtype=np.float32)
    data = np.load(EMBED_CACHE, allow_pickle=False)
    keys = [str(k) for k in data["keys"]]
    vecs = data["vecs"].astype(np.float32, copy=False)
    return {k: i for i, k in enumerate(keys)}, keys, vecs


def save_cache(keys: list[str], vecs) -> None:
    import numpy as np

    # np.savez appends .npz unless the name already ends with it
    tmp = EMBED_CACHE + ".tmp.npz"
    np.savez(tmp, keys=np.array(keys, dtype="U40"), vecs=vecs.astype(np.float32))
    os.replace(tmp, EMBED_CACHE)


def collect_texts(acts: list[str], offset: int, limit: int) -> list[str]:
    """Unique (dedup by sha1) texts: raw + expanded question, in row order."""
    expander = get_expander()
    seen: set[str] = set()
    texts: list[str] = []
    rows_kept = 0
    for act in acts:
        rows = read_jsonl(GOLD[act])
        if offset:
            rows = rows[offset:]
        if limit:
            rows = rows[:limit]
        rows_kept += len(rows)
        for g in rows:
            raw = g["question"]
            try:
                expanded = expander.expand(raw) or raw
            except Exception:
                expanded = raw
            for text in (raw, expanded):
                h = sha1(text)
                if h not in seen:
                    seen.add(h)
                    texts.append(text)
    log(f"rows={rows_kept} unique_texts={len(texts)}")
    return texts


def embed_batch(texts: list[str]) -> list[list[float]]:
    import httpx

    nim_key = os.getenv("NIM_API_KEY", "")
    nim_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    if not nim_key:
        raise SystemExit("NIM_API_KEY missing")
    payload = {
        "input": texts,
        "model": EMBED_MODEL,
        "encoding_format": "float",
        "input_type": "query",
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
            data = sorted(r.json().get("data") or [], key=lambda d: d.get("index", 0))
            vecs = [d["embedding"] for d in data]
            if len(vecs) != len(texts):
                raise RuntimeError(f"got {len(vecs)} vectors for {len(texts)} inputs")
            for v in vecs:
                if len(v) != DIM:
                    raise RuntimeError(f"dim {len(v)} != {DIM}")
            return vecs
        except Exception as exc:
            if attempt == 5:
                raise
            log(f"embed retry {attempt + 1}: {type(exc).__name__}: {exc}")
            time.sleep(delay)
            delay = min(delay * 2, 30.0)
    raise RuntimeError("unreachable")


def run(acts: list[str], offset: int, limit: int) -> int:
    index, keys, vecs = load_cache()
    log(f"cache: {len(keys)} vectors in {os.path.basename(EMBED_CACHE)}")

    texts = collect_texts(acts, offset, limit)
    missing = [t for t in texts if sha1(t) not in index]
    log(f"missing: {len(missing)} of {len(texts)}")
    if not missing:
        log("nothing to do")
        return 0

    import numpy as np

    t0 = time.time()
    done = 0
    for i in range(0, len(missing), BATCH):
        chunk = missing[i : i + BATCH]
        new_vecs = embed_batch(chunk)
        for text, vec in zip(chunk, new_vecs):
            h = sha1(text)
            if h not in index:
                index[h] = len(keys)
                keys.append(h)
        vecs = (
            np.vstack([vecs, np.array(new_vecs, dtype=np.float32)])
            if len(vecs)
            else np.array(new_vecs, dtype=np.float32)
        )
        done += len(chunk)
        save_cache(keys, vecs)  # resumable after any kill
        if (i // BATCH) % 5 == 0 or done >= len(missing):
            el = time.time() - t0
            rate = done / el if el else 0
            eta = (len(missing) - done) / rate if rate else 0
            log(f"  {done}/{len(missing)} embedded | {el:.0f}s eta={eta:.0f}s")
    log(f"done: cache now holds {len(keys)} vectors ({time.time() - t0:.0f}s)")
    return 0


def status() -> int:
    index, keys, _ = load_cache()
    total = 0
    for act, path in GOLD.items():
        rows = read_jsonl(path)
        expander = get_expander()
        need = set()
        for g in rows:
            for text in (g["question"], expander.expand(g["question"]) or g["question"]):
                need.add(sha1(text))
        hit = sum(1 for h in need if h in index)
        total += len(need)
        log(f"{act}: {hit}/{len(need)} texts embedded")
    log(f"TOTAL: {sum(1 for h in _all_needs() if h in index)}/{total}")
    return 0


def _all_needs() -> set[str]:
    expander = get_expander()
    need = set()
    for path in GOLD.values():
        for g in read_jsonl(path):
            for text in (g["question"], expander.expand(g["question"]) or g["question"]):
                need.add(sha1(text))
    return need


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", choices=sorted(GOLD), default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        return status()

    acts = sorted(GOLD) if args.all else [args.act]
    if acts == [None]:
        raise SystemExit("need --act, --all, or --status")
    return run(acts, args.offset, args.limit)


if __name__ == "__main__":
    sys.exit(main())
