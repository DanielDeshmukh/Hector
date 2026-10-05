"""Why did section_recall@10 fall 194 -> 189 when the IPC+BNS merge happened?

For every expected-section miss in iter2, report what was actually in the
retrieved top-10: how many chunks belonged to which act, and whether the
right ACT was present at all (wrong-section) or absent (crowded out by the
other code). That distinguishes 'retrieval got weaker' from 'cross-act
competition ate the top-10 slots'."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))

import run_gold_eval as rge  # noqa: E402

GOLD = {}
for line in (EVAL / "gold_iteration1.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rec = json.loads(line)
        GOLD[rec["id"]] = rec


def act_of(chunk):
    meta = chunk.get("metadata") or {}
    blob = " ".join(str(meta.get(k) or "") for k in
                    ("real_act_name", "act_name", "abbreviation", "source"))
    b = blob.lower()
    for name, key in (("IPC", "indian penal code"), ("BNS", "nyaya sanhita")):
        if key in b or name.lower() in b:
            return name
    doc = (chunk.get("document") or "")[:400].lower()
    if "indian penal code" in doc:
        return "IPC"
    if "nyaya sanhita" in doc:
        return "BNS"
    return "?"


def analyse(raw_path, label):
    rows = [json.loads(x) for x in
            Path(raw_path).read_text(encoding="utf-8").splitlines() if x.strip()]
    miss = 0
    tot = 0
    crowded = 0      # correct act present, expected section absent from top-10
    absent = 0       # correct act never retrieved at all
    detail = []
    for row in rows:
        g = GOLD.get(row["qid"])
        if not g:
            continue
        chunks = row.get("chunks") or []
        acts = [act_of(c) for c in chunks]
        for spec in g.get("expected_sections") or []:
            tot += 1
            hit = any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                      for c in chunks)
            if hit:
                continue
            miss += 1
            act, kind, num = rge.parse_section_spec(spec)
            want = "IPC" if "ipc" in act.lower() else (
                "BNS" if "bns" in act.lower() else "?")
            if want in acts:
                crowded += 1
            else:
                absent += 1
            detail.append((row["qid"], spec, want, acts))
    print(f"{label}")
    print(f"   specs={tot} hits={tot - miss} misses={miss}  "
          f"recall={(tot - miss) / tot:.4f}")
    print(f"   miss breakdown: expected act WAS retrieved but section not in "
          f"top-10 = {crowded}; expected act never retrieved = {absent}")
    for d in detail[:12]:
        print(f"     {d[0]:<16} spec={d[1]:<10} want={d[2]:<4} top10_acts={d[3]}")
    print()


analyse(EVAL / "results" / "iter2" / "raw_runs.jsonl",
        "iter2 (IPC+BNS merged index, 200q)")
analyse(EVAL / "results" / "iter1" / "raw_runs.jsonl",
        "iter1 (IPC-only index, 200q)")
