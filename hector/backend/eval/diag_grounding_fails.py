"""Inspect WHY iter2 rows fail the grounding gate: print the local verifier's
claim-by-claim breakdown for failing rows, so we can tell whether the deficit
is (a) a fixed prompt bug model-independent of the model, or (b) the model
adding detail the retrieved chunks do not support -- which is what would
decide whether swapping to nano-omni could raise the score."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW = Path(__file__).resolve().parent / "results" / "iter2" / "raw_runs.jsonl"


def main():
    rows = [
        json.loads(line)
        for line in RAW.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    tot = sum(r.get("claims_total") or 0 for r in rows)
    sup = sum(r.get("claims_supported") or 0 for r in rows)
    print(f"rows={len(rows)} claims_total={tot} claims_supported={sup} "
          f"grounded={sup / tot if tot else 0:.4f}\n")

    bad = [r for r in rows
           if (r.get("claims_supported") or 0) < (r.get("claims_total") or 0)]
    print(f"failing rows: {len(bad)}\n")

    for r in bad[:4]:
        print("=" * 78)
        print(f"qid={r['qid']}  claims {r.get('claims_supported')}/"
              f"{r.get('claims_total')}  cites={r.get('n_citations')}  "
              f"abstained={r.get('abstained')}  fabricated={r.get('fabricated')}")
        g = r.get("grounding")
        if isinstance(g, dict):
            print(f"grounding counts: mentions={g.get('n_mentions')} "
                  f"assertive={g.get('n_assertive')} negated="
                  f"{g.get('n_negated')} grounded={g.get('n_grounded')}")
            mentions = g.get("mentions") or []
            for m in mentions[:14]:
                if isinstance(m, dict):
                    ok = m.get("grounded", m.get("supported", m.get("ok")))
                    mark = "OK " if ok else "BAD"
                    txt = str(m.get("text", m.get("mention", m)))[:110]
                    print(f"   [{mark}] {txt}")
                    if not ok:
                        for k in ("reason", "why", "missing", "act",
                                  "section", "matched_in"):
                            if m.get(k):
                                print(f"        {k}: {str(m[k])[:170]}")
                else:
                    print("   -", str(m)[:150])
        elif isinstance(g, list):
            for c in g[:9]:
                print("   -", str(c)[:180])
        else:
            print("grounding field:", str(g)[:400])
        print("answer:")
        print("   ", str(r.get("answer", "")).replace("\n", " ")[:500])
    print("=" * 78)


if __name__ == "__main__":
    main()
