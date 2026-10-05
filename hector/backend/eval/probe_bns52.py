import json, os, sys, io
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
chunks = ret.search(
    q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL,
    raw_query=g["question"],
)
si = ret.last_stage_info
print("detail:", json.dumps(si.get("detail", {}), ensure_ascii=False)[:800])
print("stages:", {k: len(v) for k, v in si.get("stages", {}).items()})
for i, c in enumerate(chunks, 1):
    md = c.get("metadata") or {}
    hit = rge.section_hit(c.get("document"), md, "BNS 52")
    print(f'{i:2d} score={c.get("score"):.6f} hit={hit} act={md.get("act")} '
          f'sec={md.get("section_number")} id={c.get("id")} reasons={c.get("reasons")}')
