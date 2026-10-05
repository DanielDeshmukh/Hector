"""gen_gold_compare.py - golden questions for IPC <-> BNS comparison.

The frontend exposes a dedicated compare feature (POST /compare) and users
ask comparison questions through /ask ("Which BNS section replaced IPC 302?").
Neither was ever gate-tested: the iteration-1 gold contains zero comparison
questions (g043 was deferred because the corpus was IPC-only). This file
builds that coverage from mapping.json itself - no section numbers are
hardcoded anywhere.

Pair selection is data-driven and strict:
  * forward (IPC->BNS): every mapping entry whose BOTH sides exist as
    distinct sections in the v2 parses (this automatically drops the 74
    entries whose `new` target is > 358, i.e. sections BNS does not have);
  * reverse (BNS->IPC): only `new` values with a SINGLE ipc candidate
    (mapping.json contains 111 duplicate targets where several IPC sections
    consolidate into one BNS section - ambiguous pairs would bake one
    tie-break opinion into gold, so they are excluded rather than guessed).
  * seeded sample (SEED) of FORWARD_N / REVERSE_N pairs each.

One question per pair, two template styles alternating by index:
  * counterpart lookup ("Which BNS section corresponds to IPC {n}?")
  * side-by-side ("How does IPC {n} compare with its BNS counterpart?")
expected_sections lists BOTH sides, so section_recall only passes when
retrieval surfaces each act's own provision - the real comparison test.

expected_answer_points come from both sections' own bodies (footnotes
unwrapped, re-verified by normalised containment), so items are grounded
by construction.

Outputs in backend/eval/:
  gold_compare.jsonl             generated questions only
  gold_compare_iteration1.jsonl  generated + 21 corpus-independent guards
                                 + g043 (the human-verified comparison item)

Usage:
  python gen_gold_compare.py              # full
  python gen_gold_compare.py --limit 8    # sanity sample
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

from gen_gold_ipc import answer_points, grounded

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = os.path.abspath(os.path.join(HERE, "..", "ingest_v2"))
MAPPING = os.path.abspath(
    os.path.join(HERE, "..", "..", "api", "core", "mapping.json"))
IPC_V2 = os.path.join(INGEST, "output", "ipc-1860.jsonl")
BNS_V2 = os.path.join(INGEST, "output", "bns-2023.jsonl")
OUT_CMP = os.path.join(HERE, "gold_compare.jsonl")
OUT_IT1 = os.path.join(HERE, "gold_compare_iteration1.jsonl")
EXISTING = os.path.join(HERE, "gold_set.jsonl")

SEED = 20261013
FORWARD_N = 40
REVERSE_N = 40

# Same act-independent guards as the other golds: abstention, out-of-scope
# and prompt-injection coverage stays on every run.
CARRY_IDS = [
    "g030", "g031", "g032", "g033", "g034", "g035", "g036", "g037",
    "g040",
    "g049", "g050", "g051", "g052", "g053", "g054",
    "g055", "g056", "g057", "g058", "g059", "g060",
    # human-verified comparison item (IPC 302 -> BNS 103)
    "g043",
]

FWD_LOOKUP = (
    "Which section of the Bharatiya Nyaya Sanhita, 2023 corresponds to "
    "Section {ipc} of the Indian Penal Code ({ipc_title})?"
)
FWD_SIDE = (
    "How does Section {ipc} of the Indian Penal Code ({ipc_title}) compare "
    "with its counterpart under the Bharatiya Nyaya Sanhita?"
)
REV_LOOKUP = (
    "Which section of the Indian Penal Code is the predecessor of "
    "Section {bns} of the Bharatiya Nyaya Sanhita ({bns_title})?"
)
REV_SIDE = (
    "Compare Section {bns} of the Bharatiya Nyaya Sanhita ({bns_title}) "
    "with the corresponding provision of the Indian Penal Code."
)


def log(msg: str) -> None:
    print(f"[gen_gold_compare] {msg}", flush=True)


def load_sections(path: str) -> dict:
    """{section_number: record} keeping the first occurrence (parts deduped)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            out.setdefault(str(rec["number"]), rec)
    return out


def make_pair_question(
    direction: str, ipc_rec: dict, bns_rec: dict, i: int
) -> dict:
    ipc_n = str(ipc_rec["number"])
    bns_n = str(bns_rec["number"])
    ipc_title = re.sub(r"\s+", " ", ipc_rec.get("title") or "").strip().rstrip(".")
    bns_title = re.sub(r"\s+", " ", bns_rec.get("title") or "").strip().rstrip(".")

    ipc_pts = answer_points(ipc_rec.get("text") or "", ipc_n, ipc_title)
    bns_pts = answer_points(bns_rec.get("text") or "", bns_n, bns_title)
    ipc_doc = ipc_rec.get("embedding_text") or ""
    bns_doc = bns_rec.get("embedding_text") or ""
    if not (ipc_pts and bns_pts):
        return {}
    if not (grounded(ipc_pts, ipc_doc) and grounded(bns_pts, bns_doc)):
        return {}

    if direction == "forward":
        question = (FWD_LOOKUP if i % 2 == 0 else FWD_SIDE).format(
            ipc=ipc_n, ipc_title=ipc_title
        )
        qid = f"cmpf-{ipc_n}-{bns_n}"
        pts = (bns_pts[:2] + ipc_pts[:2])[:3]
    else:
        question = (REV_LOOKUP if i % 2 == 0 else REV_SIDE).format(
            bns=bns_n, bns_title=bns_title
        )
        qid = f"cmpr-{bns_n}-{ipc_n}"
        pts = (ipc_pts[:2] + bns_pts[:2])[:3]

    return {
        "id": qid,
        "category": "amended_or_repealed",
        "question": question,
        "expected_sections": [f"IPC {ipc_n}", f"BNS {bns_n}"],
        "expected_answer_points": pts,
        "should_abstain": False,
        "source_verified_by": "draft",
        "variant": "counterpart_lookup" if i % 2 == 0 else "side_by_side",
        "direction": direction,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    for p in (MAPPING, IPC_V2, BNS_V2):
        if not os.path.isfile(p):
            raise SystemExit(f"missing input: {p}")
    with open(MAPPING, encoding="utf-8") as fh:
        # Same shape the service uses: router._load_mapping() returns
        # mapping.json["IPC_TO_BNS"] as legal_map; the other top-level keys
        # (BNS_TO_IPC_REVERSE, SYSTEM_NOTES) are metadata, not the crosswalk.
        mapping = json.load(fh).get("IPC_TO_BNS", {})
    ipc = load_sections(IPC_V2)
    bns = load_sections(BNS_V2)
    log(f"seed={SEED} mapping entries={len(mapping)} "
        f"ipc sections={len(ipc)} bns sections={len(bns)}")

    # forward: both sides of the mapping must exist as real sections
    forward = []
    for ipc_n, mapped in mapping.items():
        bns_n = str(mapped.get("new") or "")
        if str(ipc_n) in ipc and bns_n in bns:
            forward.append((str(ipc_n), bns_n))
    # reverse: single-candidate targets only (no ambiguous consolidation)
    by_target = {}
    for ipc_n, mapped in mapping.items():
        bns_n = str(mapped.get("new") or "")
        if bns_n:
            by_target.setdefault(bns_n, []).append(str(ipc_n))
    reverse = []
    for bns_n, ipc_ns in by_target.items():
        if len(ipc_ns) != 1:
            continue
        if bns_n in bns and ipc_ns[0] in ipc:
            reverse.append((ipc_ns[0], bns_n))
    log(f"valid forward pairs={len(forward)} single-candidate reverse={len(reverse)}")

    rng = random.Random(SEED)
    fwd_pick = sorted(rng.sample(forward, min(FORWARD_N, len(forward))))
    rev_pick = sorted(rng.sample(reverse, min(REVERSE_N, len(reverse))))
    if args.limit:
        fwd_pick = fwd_pick[: args.limit]
        rev_pick = rev_pick[: args.limit]

    gen = []
    for i, (ipc_n, bns_n) in enumerate(fwd_pick):
        q = make_pair_question("forward", ipc[ipc_n], bns[bns_n], i)
        if q:
            gen.append(q)
    for i, (ipc_n, bns_n) in enumerate(rev_pick):
        q = make_pair_question("reverse", ipc[ipc_n], bns[bns_n], i)
        if q:
            gen.append(q)

    with open(OUT_CMP, "w", encoding="utf-8") as out:
        for q in gen:
            out.write(json.dumps(q, ensure_ascii=False) + "\n")
    log(f"wrote {OUT_CMP}: {len(gen)} questions "
        f"({len(fwd_pick)} forward + {len(rev_pick)} reverse requested)")

    carried = []
    if not args.limit:
        with open(EXISTING, encoding="utf-8") as fh:
            existing = {json.loads(l)["id"]: json.loads(l) for l in fh if l.strip()}
        missing = [i for i in CARRY_IDS if i not in existing]
        if missing:
            raise SystemExit(f"missing gold ids: {missing}")
        for i in CARRY_IDS:
            row = dict(existing[i])
            row.pop("variant", None)
            carried.append(row)
        log(f"carried {len(carried)} from existing set")
        with open(OUT_IT1, "w", encoding="utf-8") as out:
            for q in gen + carried:
                out.write(json.dumps(q, ensure_ascii=False) + "\n")

    ids = [q["id"] for q in gen]
    assert len(ids) == len(set(ids)), "duplicate generated ids"
    fwd = [q for q in gen if q.get("direction") == "forward"]
    rev = [q for q in gen if q.get("direction") == "reverse"]
    stats = {
        "seed": SEED,
        "generated": len(gen),
        "forward": len(fwd),
        "reverse": len(rev),
        "skipped_ungrounded": (len(fwd_pick) + len(rev_pick)) - len(gen),
        "carried": len(carried) if not args.limit else 0,
        "iteration1_total": len(gen) + len(carried) if not args.limit else None,
    }
    log("STATS " + json.dumps(stats, ensure_ascii=False))
    log("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
