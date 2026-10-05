"""gen_gold_ipc.py - golden questions for the IPC v2 book (2 per section).

Scope (user, 2026-10-03): IPC only for now; other books get their own questions
as each is v2-parsed.

Per section it emits exactly 2 questions:
  * q-a  NUMBER-FREE   - describes the subject, never says the section number.
                         This is the genuine retrieval test (mirrors the style of
                         the existing set: g003 "punishment for murder" -> BNS 103).
  * q-b  NUMBER-ANCHORED - "Section <n> ...", the natural way a user asks.

expected_sections = ["IPC <n>"] (ACT_ALIASES["IPC"] = ["indian penal code"]).
expected_answer_points are derived FROM the section body (unwrapping footnote
markers like 1[imprisonment for life]) so they are grounded by construction,
then re-verified by normalised containment against the section text.

Two outputs in backend/eval/:
  gold_set_ipc.jsonl     1,162 generated (reusable per-book artifact)
  gold_iteration1.jsonl  1,162 + 23 carried from the existing set = 1,185
                         (21 corpus-independent + g039/g041, both IPC-only)

Deferred (37 of the existing 60): 36 need other acts + g043 which also expects
BNS 103 - unattainable against an IPC-only corpus, so including it would drag
section_recall through no fault of retrieval.

Usage:
  python gen_gold_ipc.py              # full
  python gen_gold_ipc.py --limit 20   # sanity sample
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = os.path.abspath(os.path.join(HERE, "..", "ingest_v2"))
V2_RECORDS = os.path.join(INGEST, "output", "ipc-1860.jsonl")
EVAL = HERE
OUT_IPC = os.path.join(EVAL, "gold_set_ipc.jsonl")
OUT_IT1 = os.path.join(EVAL, "gold_iteration1.jsonl")
EXISTING = os.path.join(EVAL, "gold_set.jsonl")

ACT = "IPC"
SEED = 20261013

# carried over: corpus-independent (abstain / out-of-scope / injection / one
# false-premise) + the two IPC-only items. g043 excluded: expects BNS 103 too.
CARRY_IDS = [
    # corpus-independent (21)
    "g030", "g031", "g032", "g033", "g034", "g035", "g036", "g037",  # unanswerable
    "g040",                                                          # false_premise
    "g049", "g050", "g051", "g052", "g053", "g054",                  # out_of_scope
    "g055", "g056", "g057", "g058", "g059", "g060",                  # prompt_injection
    # IPC-only (2)
    "g039", "g041",
]

NO_NUM = [
    "What does the Indian Penal Code say about {t}?",
    "How does the Indian Penal Code deal with {t}?",
    "What are the provisions of the Indian Penal Code regarding {t}?",
    "Under the Indian Penal Code, what applies to {t}?",
    "What treatment does the Indian Penal Code provide for {t}?",
    "How is {t} handled under the Indian Penal Code?",
]
WITH_NUM = [
    "What does Section {n} of the Indian Penal Code provide?",
    "Explain Section {n} of the Indian Penal Code ({title}).",
    "According to Section {n} of the Indian Penal Code, what is the law on {t}?",
    "State the provisions of Section {n} of the Indian Penal Code ({title}).",
    "What does Section {n} IPC lay down about {t}?",
    "Set out what Section {n} of the Indian Penal Code says concerning {t}.",
]


def log(msg: str) -> None:
    print(f"[gen_gold] {msg}", flush=True)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def unwrap_footnotes(s: str) -> str:
    """1[imprisonment for life] -> imprisonment for life (repeat until stable)."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\d*\[([^\]]*)\]", r"\1", s)
    return s


def split_body(text: str, number: str) -> str:
    """Strip the leading '302. Title.—' and return the operative body."""
    t = unwrap_footnotes(text or "")
    t = re.sub(r"^\s*" + re.escape(str(number)) + r"\s*\.\s*", "", t)
    m = re.search(r"\.\s*[—–]\s*", t)
    body = t[m.end():] if m else t
    return re.sub(r"\s+", " ", body).strip()


# Sub-heading / amendment-reference / continuation-fragment clauses are not
# things a good answer would state, so they must not become answer points.
_AMEND = re.compile(
    r"(?:\bvide\b|\bsubs\.|\bins\.|\brep\.|\breplaced by\b|\bamended by\b"
    r"|\bw\.e\.f\.?|\bact\s+\d+\s+of\s+\d{4}|\bsec\.$)",
    re.I,
)
_HEADING = re.compile(r"^\s*of\s+[a-z]", re.I)
_FRAGMENT = re.compile(r"^\s*(?:or|and)\s*[\(\[]", re.I)


def _usable(p: str) -> bool:
    return (
        len(p) >= 30
        and not _AMEND.search(p)
        and not _HEADING.match(p)
        and not _FRAGMENT.match(p)
    )


def answer_points(text: str, number: str, title: str) -> list[str]:
    body = split_body(text, number)
    if not body:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.;])\s+", body)]
    pts = [p for p in parts if _usable(p)][:3]
    if not pts:
        # fall back to any substantive clause (headings/amendments still out)
        pts = [p for p in parts if len(p) >= 30
               and not _HEADING.match(p) and not _FRAGMENT.match(p)][:3]
    if not pts and len(body) >= 20:
        pts = [body[:300]]
    return pts


def grounded(points: list[str], doc: str) -> bool:
    """Every point must be derivable from the section text (normalised)."""
    hay = norm(unwrap_footnotes(doc))
    return all(len(p) >= 20 and norm(p) in hay for p in points)


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
        {**base, "id": f"ipc-{n}-a", "question": a, "variant": "number_free"},
        {**base, "id": f"ipc-{n}-b", "question": b, "variant": "number_anchored"},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.path.isfile(V2_RECORDS):
        raise SystemExit(f"missing v2 records: {V2_RECORDS}")
    with open(V2_RECORDS, encoding="utf-8") as fh:
        recs = [json.loads(l) for l in fh if l.strip()]
    log(f"seed={SEED} v2 records={len(recs)}")

    if args.limit:
        recs = recs[: args.limit]

    gen, skipped = [], []
    for i, rec in enumerate(recs):
        qs = make_questions(rec, i)
        if len(qs) == 2:
            gen.extend(qs)
        else:
            skipped.append(str(rec["number"]))

    with open(OUT_IPC, "w", encoding="utf-8") as out:
        for q in gen:
            out.write(json.dumps(q, ensure_ascii=False) + "\n")
    log(f"wrote {OUT_IPC}: {len(gen)} questions "
        f"({len(gen) // 2} sections x 2), skipped={len(skipped)} {skipped[:10]}")

    # assemble iteration-1 gate
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
        log(f"carried {len(carried)} from existing set "
            f"(deferred {len(existing) - len(carried)})")

        with open(OUT_IT1, "w", encoding="utf-8") as out:
            for q in gen + carried:
                out.write(json.dumps(q, ensure_ascii=False) + "\n")

    # integrity
    ids = [q["id"] for q in gen]
    assert len(ids) == len(set(ids)), "duplicate generated ids"
    expected = len(recs) * 2
    free = [q for q in gen if q["variant"] == "number_free"]
    anch = [q for q in gen if q["variant"] == "number_anchored"]
    stats = {
        "seed": SEED,
        "sections": len(recs),
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
