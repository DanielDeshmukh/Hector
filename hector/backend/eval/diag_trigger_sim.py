"""Simulate the absence-subject + inheritance rule before editing verifier.py.

Rule under test (answer-positional subject):
  for each trigger phrase occurrence in the answer:
      subject = nearest section mention starting BEFORE the trigger position
      (answer-wide); if none, nearest mention AFTER it inside the sentence.
  S = all such subjects for the answer.
  flip to negated: every assertive mention m with m.section in S
                   and m.in_sources == False  (grounded mentions untouched)
Gate = n_grounded / n_assertive (report_gates.py L116).
"""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TRIGGERS = [
    "not present in the retrieved sources",
    "not present in the sources",
    "not included in the provided sources",
    "not included in the retrieved sources",
    "missing from the sources",
    "missing from the retrieved sources",
    "consult the full text",
    "cannot be confirmed",
]
MENTION = re.compile(r"\bsection\s+(\d+[a-z]*)\b|\u00a7\u00a7?\s*(\d+[a-z]*)", re.I)
SENT = re.compile(r"(?<=[.;!?])\s+|\n+")

RUNS = [
    ("cmp1", r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\cmp1\raw_runs.jsonl"),
    ("ipc2", r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\ipc2\raw_runs.jsonl"),
    ("bns1", r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\bns1\raw_runs_gndfix.jsonl"),
]

for name, path in RUNS:
    try:
        rows = [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]
    except FileNotFoundError:
        print(f"{name}: MISSING {path}")
        continue
    G = A = GR = 0
    flips = collateral = 0
    details = []
    for r in rows:
        ans = r.get("answer") or ""
        g = r.get("grounding") or {}
        mentions = g.get("mentions") or []
        if not mentions:
            continue
        # answer-wide offsets
        spans = []
        pos = 0
        for sent in SENT.split(ans):
            if not sent.strip():
                continue
            i = ans.find(sent, pos)
            if i < 0:
                i = pos
            spans.append((i, sent))
            pos = i + len(sent)
        subjects = set()
        for i, sent in spans:
            low = sent.lower()
            trig = [t for t in TRIGGERS if t in low]
            if not trig:
                continue
            tpos = ans.find(trig[0], i)
            if tpos < 0:
                tpos = i
            before = [(m.start() + i, (m.group(1) or m.group(2)).lower())
                      for m in MENTION.finditer(sent) if m.start() + i < tpos]
            if before:
                subjects.add(before[-1][1])
            else:
                after = [(m.start() + i, (m.group(1) or m.group(2)).lower())
                         for m in MENTION.finditer(sent) if m.start() + i >= tpos]
                # only trust an after-mention in a "consult the full text"
                # sentence (mention follows the object of consulting)
                if after and ("consult the full text" in low):
                    subjects.add(after[0][1])
        G += g.get("n_grounded", 0) or 0
        A += g.get("n_assertive", 0) or 0
        GR += g.get("n_mentions", 0) or 0
        if not subjects:
            continue
        f = c = 0
        for m in mentions:
            if m.get("section") in subjects and not m.get("negated"):
                if m.get("in_sources"):
                    if m.get("grounded"):
                        c += 1
                else:
                    f += 1
        if f or c:
            details.append((r["qid"], sorted(subjects), f, c))
        flips += f
        collateral += c
    new_g, new_a = G, A - flips
    print(f"\n=== {name}: rows={len(rows)} mentions={GR} assertive={A} grounded={G}"
          f" before={G/A:.4f}" if A else f"\n=== {name}: no mentions")
    print(f"    predicted flips={flips} collateral-saved-by-gate={collateral}"
          f" after={new_g}/{new_a} = {new_g/new_a:.4f}"
          f"  gate>=0.99 -> {'PASS' if new_g/new_a >= 0.99 else 'FAIL'}")
    for qid, subs, f, c in details:
        print(f"    {qid:<16} subjects={','.join(subs):<18} flips={f} collateral={c}")
