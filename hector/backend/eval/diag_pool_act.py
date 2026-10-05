"""Does the act-aware floor stand a chance WITHOUT growing CANDIDATE_POOL?

For every section_recall miss in iter2, check whether a corpus chunk for the
expected (act, section) sits inside the reranked candidate pool
(stages.stages.rerank - the full candidate_pool before the top_k slice).

  in_pool > 0  -> a same-act floor can promote it, budget untouched
  in_pool == 0 -> the candidate pool itself is too small; must widen it"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
CORPUS = EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl"
sys.path.insert(0, str(EVAL))

import run_gold_eval as rge  # noqa: E402

GOLD = {}
for line in (EVAL / "gold_iteration1.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rec = json.loads(line)
        GOLD[rec["id"]] = rec


def load_corpus():
    """(act_code, section_number_lower) -> list of corpus ids."""
    out = {}
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        md = rec.get("metadata") or {}
        act = str(md.get("real_act_name") or "") + " " + str(md.get("act_name") or "")
        code = "ipc" if "penal code" in act.lower() else (
            "bns" if "nyaya sanhita" in act.lower() else "?")
        num = str(md.get("section_number") or "").lower()
        if code != "?" and num:
            out.setdefault((code, num), []).append(rec["id"])
    return out


def main():
    idx = load_corpus()
    rows = [json.loads(x) for x in
            (EVAL / "results" / "iter2" / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    print(f"corpus (act, section) keys: {len(idx)}\n")
    print(f"{'qid':<16} {'spec':<10} {'pool':>4} {'sec_ids':>7} {'in_pool':>7} "
          f"{'in_top10':>8}  top10 acts")
    pool_sizes = set()
    promotable = 0
    impossible = 0
    for row in rows:
        g = GOLD.get(row["qid"])
        if not g:
            continue
        chunks = row.get("chunks") or []
        hit_specs = {s for s in (g.get("expected_sections") or [])
                     if any(rge.section_hit(c.get("document"), c.get("metadata"), s)
                            for c in chunks)}
        stages = (row.get("stages") or {}).get("stages") or {}
        pool = stages.get("rerank") or []
        pool_sizes.add(len(pool))
        pool_set = set(pool)
        top10 = {c.get("id") for c in chunks}
        acts = "".join(
            "I" if "penal code" in (
                str((c.get("metadata") or {}).get("real_act_name") or "") +
                str((c.get("metadata") or {}).get("act_name") or "")).lower()
            else "B" for c in chunks)
        for spec in g.get("expected_sections") or []:
            if spec in hit_specs:
                continue
            act, _kind, num = rge.parse_section_spec(spec)
            code = "ipc" if "ipc" in act.lower() else (
                "bns" if "bns" in act.lower() else "?")
            ids = idx.get((code, (num or "").lower()), [])
            in_pool = sum(1 for i in ids if i in pool_set)
            in_top = sum(1 for i in ids if i in top10)
            if in_pool:
                promotable += 1
            else:
                impossible += 1
            print(f"{row['qid']:<16} {spec:<10} {len(pool):>4} {len(ids):>7} "
                  f"{in_pool:>7} {in_top:>8}  {acts}")
    print(f"\nobserved pool sizes: {sorted(pool_sizes)}")
    print(f"misses promotable by a same-act floor: {promotable}")
    print(f"misses NOT in pool at all (need bigger pool): {impossible}")


if __name__ == "__main__":
    main()
