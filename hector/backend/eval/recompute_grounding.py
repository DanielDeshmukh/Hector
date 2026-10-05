"""Recompute citation grounding for a completed run with the current verifier.

grounding_report() is pure text (answer + concatenated chunk documents), so
the gate can be re-measured without re-running retrieval or generation.

    python recompute_grounding.py results\\iter4

Writes <dir>/raw_runs_gndfix.jsonl (original untouched) and prints the three
gates before/after."""

import json
import math
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
os.environ.setdefault("HECTOR_GOLD_PATH", str(EVAL / "gold_iteration1.jsonl"))
os.environ.setdefault("HECTOR_EVAL_CORPUS", str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl"))
os.environ.setdefault("HECTOR_EVAL_INDEX", "hector")

import run_gold_eval as rge  # noqa: E402
from core.verifier import grounding_report  # noqa: E402

GATES = [("section_recall@10", 0.98),
         ("citation_grounded_ratio", 0.99),
         ("fabricated_free_rate", 0.991)]


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def summarize(name, rows, gold, by_qid):
    n_g = sum((r.get("grounding") or {}).get("n_grounded", 0) or 0 for r in rows)
    n_a = sum((r.get("grounding") or {}).get("n_assertive", 0) or 0 for r in rows)
    n_m = sum((r.get("grounding") or {}).get("n_mentions", 0) or 0 for r in rows)
    total = hits = 0
    for qid, g in gold.items():
        row = by_qid.get(qid)
        if row is None:
            continue
        for spec in g.get("expected_sections") or []:
            total += 1
            hits += any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                        for c in (row.get("chunks") or []))
    free = sum(1 for r in rows if not (r.get("fabricated") or []))
    return {"name": name, "n_mentions": n_m, "n_assertive": n_a, "n_grounded": n_g,
            "recall": (hits, total), "grounded": (n_g, n_a), "free": (free, len(rows)),
            "ungrounded": n_a - n_g}


def show(s):
    k, n = s["recall"]
    gk, gn = s["grounded"]
    fk, fn = s["free"]
    print(f"\n  --- {s['name']} ---")
    print(f"    mentions={s['n_mentions']} assertive={s['n_assertive']} "
          f"ungrounded={s['ungrounded']}")
    for label, (kk, nn), gate in (
        ("section_recall@10       ", s["recall"], GATES[0][1]),
        ("citation_grounded_ratio ", s["grounded"], GATES[1][1]),
        ("fabricated_free_rate    ", s["free"], GATES[2][1]),
    ):
        rate = kk / nn if nn else 0.0
        ci = wilson(kk, nn)
        print(f"    {label} {rate:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]  {kk}/{nn}"
              f"  >= {gate} -> {'PASS' if rate >= gate else 'FAIL'}")


def main(results_dir):
    results = Path(results_dir)
    rge.GOLD_SAMPLE = 200
    rge.GOLD_SAMPLE_SEED = 20261013
    gold = {g["id"]: g for g in rge.load_gold()}

    rows = [json.loads(x) for x in (results / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    by_qid = {r["qid"]: r for r in rows}
    show(summarize("BEFORE (as recorded by the run)", rows, gold, by_qid))

    out = []
    still = []
    for r in rows:
        answer = r.get("answer") or ""
        context = " ".join(c.get("document", "") for c in (r.get("chunks") or []))
        new = grounding_report(answer, context) if answer else {}
        for m in (new.get("mentions") or []):
            if not m.get("negated") and not m.get("grounded"):
                still.append((r["qid"], m.get("section"), m.get("sentence", "")[:150]))
        nr = dict(r)
        nr["grounding"] = new
        out.append(nr)

    show(summarize("AFTER (fixed verifier)", out, gold, {r["qid"]: r for r in out}))

    dest = results / "raw_runs_gndfix.jsonl"
    dest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out),
                    encoding="utf-8")
    print(f"\n  wrote {dest}")

    print(f"\n  still ungrounded assertive after the fix: {len(still)}")
    for qid, sec, sent in still:
        print(f"    {qid:<15} sec={sec:<7} {sent}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/iter4")
