"""How many same-act chunks sit ahead of the two surviving misses?

Sizes the same-act floor: for each remaining miss we print the final reranked
list tagged with its act, so we can see how many same-act chunks occupy ranks
0..k-1 and how far the target sits. The floor only needs to lift the target
into top_k by reserving slots for the act the question names."""

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

TARGETS = {"ipc-300-a": ("IPC 300", "IPC"), "ipc-499-a": ("IPC 499", "IPC")}
TOPN = 25


def act_of(md):
    blob = (str(md.get("real_act_name") or "") + " " +
            str(md.get("act_name") or "")).lower()
    return "IPC" if "penal code" in blob else (
        "BNS" if "nyaya sanhita" in blob else "?")


def main():
    stack = rge.build_stack()
    ret, expander = stack["retriever"], stack["expander"]
    rows = {r["qid"]: r for r in
            (json.loads(x) for x in
             (EVAL / "results" / "iter2" / "raw_runs.jsonl")
             .read_text(encoding="utf-8").splitlines() if x.strip())}

    for qid, (spec, want_act) in TARGETS.items():
        q = expander.expand(rows[qid]["question"])
        ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
        st = ((getattr(ret, "last_stage_info", None) or {}).get("stages") or {})
        fin = st.get("final") or []
        # rebuild act tags from corpus metadata (final ids -> corpus)
        meta = {}
        for line in CORPUS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                meta[rec["id"]] = rec.get("metadata") or {}

        same = other = 0
        target_pos = None
        ahead = None
        print(f"\n=== {qid}  ({spec}) ===")
        for i, cid in enumerate(fin[:TOPN]):
            act = act_of(meta.get(cid, {}))
            tag = act
            if act == want_act:
                same += 1
            else:
                other += 1
            md = meta.get(cid, {})
            is_target = (act == want_act and
                         str(md.get("section_number") or "").lower()
                         == spec.split()[1].lower())
            mark = ""
            if is_target:
                target_pos = i
                mark = "  <== TARGET"
            print(f"  rank {i + 1:>2} [{tag}] "
                  f"sec={str(md.get('section_number')):<7} "
                  f"{str(md.get('section_title'))[:38]}{mark}")
        # same-act count for ALL of final, and target's same-act ordinal
        all_acts = [act_of(meta.get(c, {})) for c in fin]
        ordinal = sum(1 for a in all_acts[:target_pos + 1]
                      if a == want_act) if target_pos is not None else None
        print(f"  same-act in top-{TOPN}: {same}, cross-act: {other}")
        print(f"  target at global rank {None if target_pos is None
              else target_pos + 1}; it is the {ordinal}th {want_act} chunk")
        print(f"  -> a floor of F {want_act} slots in top-{rge.TOP_K} "
              f"promotes it iff F >= {ordinal}")


if __name__ == "__main__":
    main()
