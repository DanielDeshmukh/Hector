"""gen_gold_bnss.py - golden questions for the BNSS book (2 per section).

Scope (user, 2026-10-09): the 4 indexed acts (IPC, BNS, BNSS, BSA) each get
the same 2-per-section retrieval gate. BNSS/BSA were pushed to the hector
index this session (713 vectors); this file closes their gold coverage gap
the same way gen_gold_bns.py closed BNS's.

Mirrors gen_gold_bns.py exactly, only the book and act name differ:
  * source   bnss-2023.jsonl (541 v2 records = 531 distinct sections; 10
              sections are split into parts - deduped to first occurrence
              so ids stay unique and each section gets one question pair)
  * q-a  NUMBER-FREE     "What does the Bharatiya Nagarik Suraksha Sanhita
                          say about {t}?" (the genuine retrieval test)
  * q-b  NUMBER-ANCHORED "Section {n} ..." (the natural way a user asks)
  * expected_sections = ["BNSS <n>"] (ACT_ALIASES["BNSS"] = ["bharatiya
                          nagarik suraksha sanhita"])
  * expected_answer_points derived from the section body (footnote markers
    unwrapped) and re-verified by normalised containment against
    embedding_text, so every item is grounded by construction.

Outputs in backend/eval/:
  gold_bnss.jsonl            generated questions only
  gold_bnss_iteration1.jsonl generated + the 21 act-independent
                             abstain/out-of-scope/prompt-injection guards

Usage:
  python gen_gold_bnss.py              # full
  python gen_gold_bnss.py --limit 20   # sanity sample
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

from gen_gold_ipc import answer_points, grounded

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = os.path.abspath(os.path.join(HERE, "..", "ingest_v2"))
V2_RECORDS = os.path.join(INGEST, "output", "bnss-2023.jsonl")
OUT_BNSS = os.path.join(HERE, "gold_bnss.jsonl")
OUT_IT1 = os.path.join(HERE, "gold_bnss_iteration1.jsonl")
EXISTING = os.path.join(HERE, "gold_set.jsonl")

ACT = "BNSS"
SEED = 20261013

# Carried into every run: the act-independent guards (21) keep abstention,
# out-of-scope and prompt-injection coverage on the new gold. No human-
# verified BNSS items exist yet (the deferred human set predates the
# BNSS/BSA index push).
CARRY_IDS = [
    # corpus-independent (21)
    "g030", "g031", "g032", "g033", "g034", "g035", "g036", "g037",
    "g040",
    "g049", "g050", "g051", "g052", "g053", "g054",
    "g055", "g056", "g057", "g058", "g059", "g060",
]

NO_NUM = [
    "What does the Bharatiya Nagarik Suraksha Sanhita say about {t}?",
    "How does the Bharatiya Nagarik Suraksha Sanhita deal with {t}?",
    "What are the provisions of the Bharatiya Nagarik Suraksha Sanhita regarding {t}?",
    "Under the Bharatiya Nagarik Suraksha Sanhita, what applies to {t}?",
    "What treatment does the Bharatiya Nagarik Suraksha Sanhita provide for {t}?",
    "How is {t} handled under the Bharatiya Nagarik Suraksha Sanhita?",
]
WITH_NUM = [
    "What does Section {n} of the Bharatiya Nagarik Suraksha Sanhita provide?",
    "Explain Section {n} of the Bharatiya Nagarik Suraksha Sanhita ({title}).",
    "According to Section {n} of the Bharatiya Nagarik Suraksha Sanhita, what is the law on {t}?",
    "State the provisions of Section {n} of the Bharatiya Nagarik Suraksha Sanhita ({title}).",
    "What does Section {n} BNSS lay down about {t}?",
    "Set out what Section {n} of the Bharatiya Nagarik Suraksha Sanhita says concerning {t}.",
]


def log(msg: str) -> None:
    print(f"[gen_gold_bnss] {msg}", flush=True)


def make_questions(rec: dict, i: int) -> list[dict]:
    n = str(rec["number"])
    title = (rec.get("title") or "").strip() or f"Section {n}"
    t = re.sub(r"\s+", " ", title).lower().rstrip(".")
    text = rec.get("text") or ""
    doc = rec.get("embedding_text") or ""

    pts = answer_points(text, n, title)
    if not pts or not grounded(pts, doc):
        return []  # never emit an ungrounded item

    spec = [f"{ACT} {n}"]
    a = NO_NUM[i % len(NO_NUM)].format(t=t, n=n, title=title)
    b = WITH_NUM[(i * 5 + 1) % len(WITH_NUM)].format(t=t, n=n, title=title)
    if a == b:
        b = WITH_NUM[(i * 5 + 2) % len(WITH_NUM)].format(t=t, n=n, title=title)

    base = {
        "category": "answerable",
        "expected_sections": spec,
        "expected_answer_points": pts,
        "should_abstain": False,
        "source_verified_by": "draft",
    }
    return [
        {**base, "id": f"bnss-{n}-a", "question": a, "variant": "number_free"},
        {**base, "id": f"bnss-{n}-b", "question": b, "variant": "number_anchored"},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.path.isfile(V2_RECORDS):
        raise SystemExit(f"missing v2 records: {V2_RECORDS}")
    with open(V2_RECORDS, encoding="utf-8") as fh:
        recs = [json.loads(l) for l in fh if l.strip()]

    # 10 sections are split into parts (same number + title, different
    # clauses); keep the first occurrence so each section yields one pair.
    seen, sections = set(), []
    for rec in recs:
        n = str(rec["number"])
        if n in seen:
            continue
        seen.add(n)
        sections.append(rec)
    log(f"seed={SEED} v2 records={len(recs)} distinct sections={len(sections)}")

    if args.limit:
        sections = sections[: args.limit]

    gen, skipped = [], []
    for i, rec in enumerate(sections):
        qs = make_questions(rec, i)
        if len(qs) == 2:
            gen.extend(qs)
        else:
            skipped.append(str(rec["number"]))

    with open(OUT_BNSS, "w", encoding="utf-8") as out:
        for q in gen:
            out.write(json.dumps(q, ensure_ascii=False) + "\n")
    log(f"wrote {OUT_BNSS}: {len(gen)} questions "
        f"({len(gen) // 2} sections x 2), skipped={len(skipped)} {skipped[:10]}")

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
    expected = len(sections) * 2
    free = [q for q in gen if q["variant"] == "number_free"]
    anch = [q for q in gen if q["variant"] == "number_anchored"]
    stats = {
        "seed": SEED,
        "sections": len(sections),
        "generated": len(gen),
        "expected_2x": expected,
        "number_free": len(free),
        "number_anchored": len(anch),
        "skipped_ungrounded": skipped,
        "carried": len(carried) if not args.limit else 0,
        "iteration1_total": len(gen) + len(carried) if not args.limit else None,
    }
    log("STATS " + json.dumps(stats, ensure_ascii=False))
    if len(gen) != expected:
        log(f"FAIL: expected {expected} generated, got {len(gen)}")
        return 3
    log("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
