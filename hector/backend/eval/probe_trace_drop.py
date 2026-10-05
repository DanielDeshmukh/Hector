"""Where does the expected section disappear?

Replays each section_recall miss through retriever.search() using the SAME
expanded query the run used, then reports the first stage id at which the
corpus id for the expected (act, section) is no longer present:

    dense -> bm25 -> rrf -> scored -> dedup -> rerank -> threshold -> final

That pinpoints whether the fix belongs in the query expander, the fusion/scoring,
dedup, the cross-encoder rerank, or the relevance threshold."""

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

STAGES = ["dense", "bm25", "rrf", "scored", "dedup", "rerank", "threshold",
          "final"]


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
    ret = stack["retriever"]
    print("[stack] ready\n")

    rows = [json.loads(x) for x in
            (EVAL / "results" / "iter2" / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]

    # where the id was last seen, per miss
    tally = {}
    print(f"{'qid':<16} {'spec':<10} last seen at / never seen at")
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
            want = set(keys.get((code, (num or "").lower()), []))
            if not want:
                continue
            q = row.get("expanded") or row.get("question") or ""
            ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
            info = getattr(ret, "last_stage_info", None) or {}
            st = info.get("stages") or {}
            last = None
            for name in STAGES:
                ids = set(st.get(name) or [])
                if ids & want:
                    last = name
            # first stage where it is absent after having been present
            lost_at = None
            seen = False
            for name in STAGES:
                ids = set(st.get(name) or [])
                present = bool(ids & want)
                if present:
                    seen = True
                elif seen and lost_at is None:
                    lost_at = name
            tally[(last, lost_at)] = tally.get((last, lost_at), 0) + 1
            print(f"{row['qid']:<16} {spec:<10} "
                  f"last_seen={str(last):<9} lost_at={lost_at}")
    print("\nsummary (last_seen, lost_at):")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
