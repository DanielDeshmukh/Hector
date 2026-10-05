import json, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
EVAL = r"D:\Vs Code\VS code\Hector\hector\backend\eval"
os.environ.setdefault("HECTOR_GOLD_PATH", os.path.join(EVAL, "gold_bns_iteration1.jsonl"))
os.environ["HECTOR_EVAL_CORPUS"] = os.path.join(
    os.path.dirname(EVAL), "ingest_v2", "output", "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\backend")
for line in open(r"D:\Vs Code\VS code\Hector\.env", encoding="utf-8"):
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import run_gold_eval as rge
g = None
for line in open(os.environ["HECTOR_GOLD_PATH"], encoding="utf-8"):
    rec = json.loads(line)
    if rec["id"] == "bns-52-a":
        g = rec
        break
stack = rge.build_stack()
ret, exp = stack["retriever"], stack["expander"]
q = exp.expand(g["question"]) or g["question"]
print("RAW :", g["question"])
print("EXP :", q)
print()
from data.hybrid_retriever import SECTION_PATTERN, ACT_PATTERN
print("SECTION_PATTERN finds:", SECTION_PATTERN.findall(q))
print("ACT_PATTERN finds:", ACT_PATTERN.findall(q))
pq = ret._parse_query(q)
print("parse_query:", pq)
cited = ret._cited_act_sections(q, pq)
print("cited_act_sections:", cited)
rows = ret._citation_injection_rows(q, pq)
print(f"injection rows ({len(rows)}):")
for r in rows[:15]:
    print("  ", r["id"], r["reasons"][:1], r.get("metadata", {}).get("section_number"))
