import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
raw_path = r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\cmp1\raw_runs.jsonl"
rows = [json.loads(x) for x in open(raw_path, encoding="utf-8") if x.strip()]
n_un = 0
for r in rows:
    g = r.get("grounding") or {}
    mentions = g.get("mentions") or []
    un = [m for m in mentions if not m.get("negated") and not m.get("grounded")]
    if un:
        n_un += len(un)
        secs = []
        for c in (r.get("chunks") or []):
            meta = c.get("metadata") or {}
            s = meta.get("section_number")
            act = meta.get("act", "?")
            secs.append(f"{act}:{s}")
        print("=" * 100)
        print(f"{r['qid']}  ungrounded={len(un)}  chunk_sections={secs}")
        for m in un:
            print(f"  sec={m.get('section')} neg={m.get('negated')} :: {m.get('sentence','')}")
print(f"\ntotal ungrounded assertive: {n_un}")
