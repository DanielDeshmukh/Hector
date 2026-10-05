"""Probe: would an act-filtered dense leg recover the sections that a plain
top-30 dense query never returns?

For each section_recall miss we compare three candidate-pool constructions
against the corpus id for the expected (act, section):

  plain-30      what the retriever does today (no filter)
  filtered-30   dense query restricted to the act the question names
  blended       filtered-30 + plain-30 merged (floor keeps cross-act chunks
                available for the IPC/BNS comparison, so filtering never
                removes them - it only guarantees same-act slots)

A miss is recoverable when the expected id lands in the pool that would
feed the reranker."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
CORPUS = EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl"

for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))

# env the stack needs
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        sys.modules.setdefault("os", __import__("os"))
        import os as _os
        _os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import os  # noqa: E402

os.environ["HECTOR_EVAL_CORPUS"] = str(CORPUS)
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402

GOLD = {}
for line in (EVAL / "gold_iteration1.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rec = json.loads(line)
        GOLD[rec["id"]] = rec


def corpus_ids():
    """(act_code, section_lower) -> list of ids; also id -> (act, sec)."""
    by_key, meta = {}, {}
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        md = rec.get("metadata") or {}
        blob = (str(md.get("real_act_name") or "") + " " +
                str(md.get("act_name") or "")).lower()
        code = "ipc" if "penal code" in blob else (
            "bns" if "nyaya sanhita" in blob else "?")
        sec = str(md.get("section_number") or "").lower()
        if code != "?" and sec:
            by_key.setdefault((code, sec), []).append(rec["id"])
            meta[rec["id"]] = (code, sec, str(md.get("abbreviation") or ""))
    return by_key, meta


def ids_from(matches):
    return [m.get("id") for m in (matches or [])]


def main():
    by_key, id_meta = corpus_ids()
    stack = rge.build_stack()
    ret = stack["retriever"]
    idx = ret.pinecone_index
    print("[stack] ready\n")

    rows = [json.loads(x) for x in
            (EVAL / "results" / "iter2" / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    by_qid = {r["qid"]: r for r in rows}

    target = [q for q in by_qid]  # all, filtered below to the misses
    stats = {"plain": 0, "filtered": 0, "blended": 0, "total": 0}
    print(f"{'qid':<16} {'spec':<10} {'plain30':>8} {'filt30':>8} {'blend':>7}")
    for row in rows:
        g = GOLD.get(row["qid"])
        if not g:
            continue
        chunks = row.get("chunks") or []
        for spec in g.get("expected_sections") or []:
            if any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                   for c in chunks):
                continue
            act, _kind, num = rge.parse_section_spec(spec)
            code = "ipc" if "ipc" in act.lower() else "bns"
            want = by_key.get((code, (num or "").lower()), [])
            if not want:
                continue
            stats["total"] += 1
            emb = ret._embed_text(row["question"])
            plain = ids_from(idx.query(vector=emb, top_k=30,
                                       include_metadata=True).get("matches"))
            flt = ids_from(idx.query(
                vector=emb, top_k=30, include_metadata=True,
                filter={"abbreviation": {"$in": ["Indian Penal Code",
                                                 "Bharatiya Nyaya Sanhita"]}}
                if code == "ipc" else
                {"abbreviation": {"$in": ["Bharatiya Nyaya Sanhita",
                                          "Indian Penal Code"]}}
            ).get("matches"))
            # act-correct filter: only the act we want
            flt = [i for i in flt if id_meta.get(i, ("?",))[0] == code]
            blended = list(dict.fromkeys(flt + plain))
            p = any(w in plain for w in want)
            f = any(w in flt for w in want)
            b = any(w in blended for w in want)
            stats["plain"] += p
            stats["filtered"] += f
            stats["blended"] += b
            print(f"{row['qid']:<16} {spec:<10} {str(p):>8} {str(f):>8} "
                  f"{str(b):>7}")
    print(f"\npool presence for the {stats['total']} misses "
          f"(need >=6 recoverable to clear 0.98):")
    print(f"   plain-30   : {stats['plain']}")
    print(f"   filtered-30: {stats['filtered']}")
    print(f"   blended    : {stats['blended']}")


if __name__ == "__main__":
    main()
