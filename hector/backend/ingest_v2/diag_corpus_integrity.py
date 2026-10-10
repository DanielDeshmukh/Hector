"""Diagnostic: verify no cross-act leakage / id-mapping breaks in eval_corpus.jsonl."""
import json, collections, sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Vs Code\VS code\Hector\hector\backend\ingest_v2\output\eval_corpus.jsonl"

acts = collections.Counter()
bad = []           # id/act_id prefix mismatch
ids_seen = set()
dup_ids = []
missing_meta = []
sections_per_act = collections.defaultdict(list)

with open(path, encoding="utf-8") as f:
    for i, ln in enumerate(f, 1):
        row = json.loads(ln)
        meta = row.get("metadata") or {}
        aid = meta.get("act_id", "MISSING")
        acts[aid] += 1
        rid = row.get("id", "MISSING")
        if rid in ids_seen:
            dup_ids.append(rid)
        ids_seen.add(rid)
        if not rid.startswith(str(aid) + "::"):
            bad.append((i, rid, aid))
        for k in ("act_name", "year", "section_number"):
            if k not in meta:
                missing_meta.append((i, rid, k))
        sections_per_act[aid].append(meta.get("section_number", "?"))

print("Records per act_id:")
for a, c in sorted(acts.items()):
    secs = sections_per_act[a]
    uniq = len(set(secs))
    print(f"  {a}: {c} records, {uniq} unique section_numbers")
print(f"TOTAL: {sum(acts.values())}")
print(f"\nDuplicate record ids: {len(dup_ids)}")
if dup_ids:
    print("  sample:", dup_ids[:10])
print(f"id/act_id prefix mismatches: {len(bad)}")
if bad:
    for b in bad[:10]:
        print("  ", b)
print(f"Missing required meta keys: {len(missing_meta)}")
if missing_meta:
    for m in missing_meta[:10]:
        print("  ", m)

# cross-act section number collisions (same section_number under 2+ act_ids)
sec_to_acts = collections.defaultdict(set)
for aid, secs in sections_per_act.items():
    for s in secs:
        sec_to_acts[s].add(aid)
collisions = {s: sorted(a) for s, a in sec_to_acts.items() if len(a) > 1}
print(f"\nSection numbers appearing under multiple act_ids: {len(collisions)}")
for s in sorted(collisions, key=lambda x: (str(x)))[:20]:
    print(f"  section {s}: {collisions[s]}")
