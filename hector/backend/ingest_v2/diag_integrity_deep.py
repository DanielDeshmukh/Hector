"""Deep integrity + cross-act leakage check across all v2 jsonl acts + IEA pilot."""
import json, os, collections, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

ACT_FILES = ["ipc-1860", "bns-2023", "bnss-2023", "bsa-2023", "iea-1872"]

# 1. Per-act schema check + id prefix
print("=" * 70)
print("1. PER-ACT SCHEMA + ID PREFIX CHECK")
print("=" * 70)

expected_keys = None
all_ok = True
for act in ACT_FILES:
    path = os.path.join(OUT, f"{act}.jsonl")
    if not os.path.isfile(path):
        print(f"  {act}: MISSING")
        all_ok = False
        continue
    with open(path, encoding="utf-8") as f:
        recs = [json.loads(ln) for ln in f if ln.strip()]
    if not recs:
        print(f"  {act}: EMPTY")
        all_ok = False
        continue
    keys0 = set(recs[0].keys())
    if expected_keys is None:
        expected_keys = keys0
    key_mismatch = keys0 ^ expected_keys
    # id prefix + act_id consistency
    bad_id = [r["id"] for r in recs if not r["id"].startswith(act + ":")]
    bad_aid = [r["id"] for r in recs if r.get("act_id") != act]
    # number uniqueness within act
    nums = [str(r.get("number")) for r in recs]
    dup_nums = [n for n, c in collections.Counter(nums).items() if c > 1]
    # empty texts
    empty_t = sum(1 for r in recs if not (r.get("text") or "").strip())
    empty_e = sum(1 for r in recs if not (r.get("embedding_text") or "").strip())
    # content_hash present
    no_hash = sum(1 for r in recs if not r.get("content_hash"))
    # page sanity
    bad_pages = [r["id"] for r in recs
                 if r.get("page_start") is None or r.get("page_end") is None
                 or r["page_end"] < r["page_start"]]
    status = "OK" if not (key_mismatch or bad_id or bad_aid or empty_t
                          or empty_e or no_hash or bad_pages) else "PROBLEM"
    if status == "PROBLEM":
        all_ok = False
    print(f"  {act}: {len(recs)} recs | schema={'match' if not key_mismatch else 'DIFF ' + str(sorted(key_mismatch))[:60]} "
          f"| bad_id={len(bad_id)} bad_act_id={len(bad_aid)} dup_sec={len(dup_nums)} "
          f"| empty_text={empty_t} empty_emb={empty_e} no_hash={no_hash} bad_pages={len(bad_pages)} "
          f"| {status}")

# 2. Cross-act: no record's text should contain another act's short name header
print()
print("=" * 70)
print("2. CROSS-ACT TEXT LEAKAGE (section text must not cite wrong act id)")
print("=" * 70)
# The record's own act_id in text is normal (e.g. "IPC" in IPC text).
# Leakage = an IPC record whose embedding_text starts with "BNS" header,
# or whose first 200 chars mention the other act's act_id as if it were the source.
act_to_id = {
    "ipc-1860": ["IPC", "Indian Penal Code"],
    "bns-2023": ["BNS", "Bharatiya Nyaya Sanhita"],
    "bnss-2023": ["BNSS", "Bharatiya Nagarik Suraksha Sanhita"],
    "bsa-2023": ["BSA", "Bharatiya Sakshya Adhiniyam"],
    "iea-1872": ["IEA", "Indian Evidence Act"],
}
# For each record, check embedding_text first line for wrong-act markers
leaks = []
for act in ACT_FILES:
    path = os.path.join(OUT, f"{act}.jsonl")
    if not os.path.isfile(path):
        continue
    with open(path, encoding="utf-8") as f:
        recs = [json.loads(ln) for ln in f if ln.strip()]
    others = {a: names for a, names in act_to_id.items() if a != act}
    for r in recs:
        et = (r.get("embedding_text") or "")[:300]
        # IPC section text legitimately says "Indian Penal Code" in titles;
        # only flag if another act's NAME appears as a header pattern in first line
        first_line = et.split("\n", 1)[0]
        for other_act, names in others.items():
            for name in names:
                # header-style: "BNS Section" or "Bharatiya Nyaya Sanhita Section"
                if re.search(rf"\b{re.escape(name)}\s+Section\b", first_line, re.I):
                    leaks.append((act, r["id"], name, first_line[:80]))
                    break
print(f"  Wrong-act header leaks in first line: {len(leaks)}")
for l in leaks[:10]:
    print("   ", l)

# 3. IEA-specific: check registry year/act_name vs records
print()
print("=" * 70)
print("3. IEA-1872 RECORD vs REGISTRY")
print("=" * 70)
try:
    import yaml
    reg = yaml.safe_load(open(os.path.join(HERE, "act_registry.yaml"), encoding="utf-8"))
    iea = next(a for a in reg["acts"] if a["act_id"] == "iea-1872")
    print(f"  registry: act_name={iea.get('act_name')!r} year={iea.get('year')} "
          f"act_short={iea.get('act_short')!r}")
    with open(os.path.join(OUT, "iea-1872.jsonl"), encoding="utf-8") as f:
        recs = [json.loads(ln) for ln in f if ln.strip()]
    bad_name = [r["id"] for r in recs if r.get("act_name") != iea["act_name"]]
    bad_short = [r["id"] for r in recs if r.get("act_short") != iea["act_short"]]
    print(f"  records: {len(recs)} | act_name mismatch={len(bad_name)} "
          f"act_short mismatch={len(bad_short)}")
    # sample a few records
    for r in recs[:3]:
        print(f"    sample: id={r['id']} number={r.get('number')} "
              f"title={r.get('title')[:50]!r} pages={r.get('page_start')}-{r.get('page_end')}")
except Exception as e:
    print(f"  ERROR: {e}")

# 4. eval_corpus act_id distribution + id format
print()
print("=" * 70)
print("4. EVAL_CORPUS.JSONL ACT_ID DISTRIBUTION")
print("=" * 70)
corp = os.path.join(OUT, "eval_corpus.jsonl")
acts = collections.Counter()
bad_fmt = 0
with open(corp, encoding="utf-8") as f:
    for ln in f:
        row = json.loads(ln)
        aid = row["metadata"].get("act_id")
        acts[aid] += 1
        if not row["id"].startswith(aid + ":"):
            bad_fmt += 1
for a, c in sorted(acts.items()):
    print(f"  {a}: {c}")
print(f"  TOTAL: {sum(acts.values())} | id_format_violations: {bad_fmt}")

print()
print("=" * 70)
print("OVERALL:", "ALL CHECKS PASS" if all_ok and not leaks and bad_fmt == 0 else "ISSUES FOUND")
print("=" * 70)
