import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
raw_path = r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\cmp1\raw_runs.jsonl"
rows = [json.loads(x) for x in open(raw_path, encoding="utf-8") if x.strip()]

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

def grounding_lookup(r):
    g = r.get("grounding") or {}
    return {(m.get("section"), m.get("sentence", "")[:60]): m for m in (g.get("mentions") or [])}

print("sentences containing a trigger phrase + nearest preceding mention:")
n_trig = 0
for r in rows:
    ans = r.get("answer") or ""
    g = r.get("grounding") or {}
    mentions = g.get("mentions") or []
    for sent in SENT.split(ans):
        low = sent.lower()
        trig = [t for t in TRIGGERS if t in low]
        if not trig:
            continue
        # nearest mention starting before the first trigger occurrence
        pos = low.find(trig[0])
        subs = [(m.start(), (m.group(1) or m.group(2)).lower()) for m in MENTION.finditer(sent) if m.start() < pos]
        if not subs:
            print(f"  [NO-MENTION-BEFORE] {r['qid']}: {sent.strip()[:150]}")
            continue
        n_trig += 1
        sec = subs[-1][1]
        # is there an assertive ungrounded mention of this section in this answer?
        rel = [m for m in mentions if m.get("section") == sec]
        stat = [(m.get("negated"), m.get("in_sources"), m.get("grounded")) for m in rel]
        print(f"  {r['qid']:<16} trigger={trig[0]:<38} subject={sec:<6} mentions(neg,in,grd)={stat}  sent={sent.strip()[:90]}")
print(f"\ntrigger sentences with a preceding mention: {n_trig}")

# also: for each candidate subject section, are ALL its mentions ungrounded?
print("\nsubject sections where some mention is grounded (collateral risk):")
risk = {}
for r in rows:
    ans = r.get("answer") or ""
    mentions = (r.get("grounding") or {}).get("mentions") or []
    for sent in SENT.split(ans):
        low = sent.lower()
        trig = [t for t in TRIGGERS if t in low]
        if not trig:
            continue
        pos = low.find(trig[0])
        subs = [(m.start(), (m.group(1) or m.group(2)).lower()) for m in MENTION.finditer(sent) if m.start() < pos]
        if subs:
            sec = subs[-1][1]
            for m in mentions:
                if m.get("section") == sec and m.get("grounded"):
                    risk.setdefault((r["qid"], sec), 0)
                    risk[(r["qid"], sec)] += 1
for k, v in risk.items():
    print("  RISK", k, v)
if not risk:
    print("  none")
