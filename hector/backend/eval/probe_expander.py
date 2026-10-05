"""Is the QUERY EXPANDER what loses the expected section from dense top-30?

The raw-question probe put all 9 expected sections inside plain dense top-30,
yet replaying the run's EXPANDED query shows 5 never appear at any stage.
This replays both forms for the 5 and reports dense/final presence, which
isolates the expander as the cause versus a fusion/rerank problem."""

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

FOCUS = {"ipc-275-b", "ipc-263A-b", "ipc-8-b", "ipc-313-b", "ipc-252-b",
         "ipc-300-a"}  # 5 never-seen + 1 ranked-below-10 as a control


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


def probe(ret, q, want):
    ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
    st = ((getattr(ret, "last_stage_info", None) or {}).get("stages") or {})
    dense = set(st.get("dense") or [])
    final = set(st.get("final") or [])
    fin_ids = st.get("final") or []
    pos = next((i for i, x in enumerate(fin_ids) if x in want), None)
    return bool(dense & want), bool(final & want), pos


def main():
    keys = load_keys()
    stack = rge.build_stack()
    ret = stack["retriever"]
    print("[stack] ready\n")
    rows = [json.loads(x) for x in
            (EVAL / "results" / "iter2" / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]

    print(f"{'qid':<14} {'spec':<9} {'expanded: dense/final/pos':<30} "
          f"{'raw: dense/final/pos'}")
    exp_recover = raw_recover = 0
    n = 0
    for row in rows:
        if row["qid"] not in FOCUS:
            continue
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
            want = set(keys.get((code, (num or "").lower()), []))
            if not want:
                continue
            n += 1
            e = probe(ret, row.get("expanded") or row.get("question") or "", want)
            r = probe(ret, row.get("question") or "", want)
            exp_recover += e[0]
            raw_recover += r[0]
            print(f"{row['qid']:<14} {spec:<9} "
                  f"{'dense=%s final=%s pos=%s' % e:<30} "
                  f"dense={r[0]} final={r[1]} pos={r[2]}")
    print(f"\nexpected section present in DENSE top-30 for these {n} misses:")
    print(f"   using the run's expanded query : {exp_recover}/{n}")
    print(f"   using the raw question         : {raw_recover}/{n}")


if __name__ == "__main__":
    main()
