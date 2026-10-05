import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
raw_path = r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\bns1\raw_runs.jsonl"
want = {"bns-39-b", "bns-307-a", "bns-87-a", "bns-310-b", "bns-275-a", "bns-2-a"}
rows = {json.loads(x)["qid"]: json.loads(x) for x in open(raw_path, encoding="utf-8") if x.strip()}
for qid in sorted(want):
    r = rows[qid]
    print("=" * 100)
    secnums = set()
    for c in r.get("chunks") or []:
        md = c.get("metadata") or {}
        secnums.add(str(md.get("section_number")))
    print(f"{qid}  n_chunks={r.get('n_chunks')}  chunk_sections={sorted(secnums, key=lambda s: (len(s), s))}")
    ans = r.get("answer") or ""
    for m in (r.get("grounding") or {}).get("mentions") or []:
        if m.get("grounded") or m.get("negated"):
            continue
        print(f'  UNGROUNDED sec={m.get("section")} neg={m.get("negated")} :: {m.get("sentence")[:220]}')
    # context around each ungrounded section number in the answer
    for m in (r.get("grounding") or {}).get("mentions") or []:
        if m.get("grounded") or m.get("negated"):
            continue
        num = str(m.get("section"))
        for pat in (rf"Section\s+{re.escape(num)}\b", rf"§\s*{re.escape(num)}\b"):
            mm = re.search(pat, ans)
            if mm:
                a = max(0, mm.start() - 260)
                print(f"  CTX[{num}]: ...{ans[a:mm.end()+200]}...".replace("\n", " "))
                break
