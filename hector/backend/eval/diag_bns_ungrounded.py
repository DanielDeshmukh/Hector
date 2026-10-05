import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
raw_path = r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\bns1\raw_runs.jsonl"
rows = [json.loads(x) for x in open(raw_path, encoding="utf-8") if x.strip()]
print("row keys:", sorted(rows[0].keys()))
n_un = 0
for r in rows:
    g = r.get("grounding") or {}
    detail = g.get("details") or g.get("mentions") or g.get("ungrounded") or None
    un = (g.get("n_assertive", 0) or 0) - (g.get("n_grounded", 0) or 0)
    if un > 0:
        n_un += un
        print(f"\n{r['qid']} ungrounded={un} keys_detail={type(detail).__name__}")
        if isinstance(detail, list):
            for d in detail:
                if isinstance(d, dict):
                    if d.get("grounded") is False or d.get("ungrounded") or d.get("ok") is False:
                        print("   ", json.dumps(d, ensure_ascii=False)[:400])
        # show grounding subkeys once
        print("   grounding keys:", sorted(g.keys()))
print(f"\ntotal ungrounded mentions: {n_un}")
