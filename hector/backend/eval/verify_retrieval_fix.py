"""Verify the expander fix against the 9 section_recall misses.

For each miss, expand the question with the PATCHED expander (section-citing
queries now pass through unchanged), search with the real stack, and report
whether the expected corpus id makes the final top-10 - i.e. section_hit.

    dense  : expected id in dense leg top-30
    pos    : position in final reranked list (None = absent)
    hit    : pos is not None and pos < TOP_K   (counts toward section_recall@10)

Ground truth before the fix (iter2 run): all 9 were misses -> 189/198 = 0.9545."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
CORPUS = EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl"
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))

import os  # noqa: E402
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
os.environ["HECTOR_EVAL_CORPUS"] = str(CORPUS)
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402

GOLD = {}
for line in (EVAL / "gold_iteration1.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rec = json.loads(line)
        GOLD[rec["id"]] = rec

MISSES = [("ipc-275-b", "IPC 275"), ("ipc-263A-b", "IPC 263A"),
          ("ipc-8-b", "IPC 8"), ("ipc-300-a", "IPC 300"),
          ("ipc-351-b", "IPC 351"), ("ipc-313-b", "IPC 313"),
          ("ipc-53A-b", "IPC 53A"), ("ipc-252-b", "IPC 252"),
          ("ipc-499-a", "IPC 499")]


def load_keys():
    out = {}
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
            out.setdefault((code, sec), []).append(rec["id"])
    return out


def main():
    keys = load_keys()
    stack = rge.build_stack()
    ret, expander = stack["retriever"], stack["expander"]
    print("[stack] ready\n")

    rows = {r["qid"]: r for r in
            (json.loads(x) for x in
             (EVAL / "results" / "iter2" / "raw_runs.jsonl")
             .read_text(encoding="utf-8").splitlines() if x.strip())}

    hits = 0
    print(f"{'qid':<14} {'spec':<9} {'expanded?':<10} {'dense':>6} "
          f"{'pos':>5} {'hit@10':>7}")
    for qid, spec in MISSES:
        row = rows[qid]
        q = row["question"]
        expanded = expander.expand(q)
        changed = "yes" if expanded != q else "NO (kept)"
        act, _k, num = rge.parse_section_spec(spec)
        code = "ipc" if "ipc" in act.lower() else "bns"
        want = set(keys.get((code, (num or "").lower()), []))

        ret.search(expanded, top_k=rge.TOP_K,
                   candidate_pool=rge.CANDIDATE_POOL, raw_query=q)
        st = ((getattr(ret, "last_stage_info", None) or {}).get("stages") or {})
        fin = st.get("final") or []
        dense = bool(set(st.get("dense") or []) & want)
        pos = next((i for i, x in enumerate(fin) if x in want), None)
        hit = pos is not None and pos < rge.TOP_K
        hits += hit
        print(f"{qid:<14} {spec:<9} {changed:<10} {str(dense):>6} "
              f"{str(pos):>5} {str(hit):>7}")

    print(f"\nmisses recovered into top-10: {hits}/9")
    print(f"projected section_recall@10: "
          f"{189 + hits}/198 = {(189 + hits) / 198:.4f} "
          f"(need >= 0.9800 -> {int(-(-0.98 * 198))} hits)")


if __name__ == "__main__":
    main()
