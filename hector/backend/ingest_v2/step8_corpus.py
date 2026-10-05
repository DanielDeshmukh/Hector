"""step8_corpus.py - build the eval corpus for hector-legal-v2.

Scope decision (user, 2026-10-03): hector-legal-v2 holds the v2-parsed records
for the two acts live this month - IPC and BNS. Both have to share one index
because they answer each other: the generator's IPC<->BNS comparison is only
groundable once the BNS text is retrievable. BNSS/BSA are parsed but deferred
to the one-book-per-week cadence. The old Chroma/legacy parse of the other
books is deliberately NOT mixed in, so every metric number describes validated
v2 data only (old IPC is likewise excluded - it never passed the v2 gates).

Reads  output/<act_id>.jsonl (the 27-key v2 records), one act or several.
Writes output/eval_corpus.jsonl  {id, document, metadata} per line.

`document` = embedding_text (581/581 IPC contain "Section <n>", which the eval's
section_hit regexes require; the verbatim `text` field only does on 5/581).
`metadata` omits `document` here - step9_push.py copies it in at upsert time so
the Pinecone dense leg can return text.

Usage:
  python step8_corpus.py
  python step8_corpus.py --act ipc-1860
  python step8_corpus.py --act ipc-1860,bns-2023
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2_OUT = os.path.join(HERE, "output")
CORPUS_PATH = os.path.join(V2_OUT, "eval_corpus.jsonl")
SEED = 20261013  # printed for traceability; build is fully deterministic (no RNG)


def log(msg: str) -> None:
    print(f"[step8] {msg}", flush=True)


def v2_metadata(rec: dict) -> dict:
    """Map a 27-key v2 record onto the citation metadata contract.

    Keys are the ones the stack actually reads (see response_generator
    LegalCitation, hybrid_retriever._infer_act / _extract_document_citation,
    run_gold_eval.section_hit).
    """
    return {
        "act_name": rec["act_name"],                  # fallback act everywhere
        "real_act_name": rec["act_name"],             # section_hit alias match
        "abbreviation": rec["act_short"],
        "section_number": str(rec["number"]),         # citation + $eq filter
        "section_title": rec.get("title"),
        "chapter": rec.get("chapter"),                # citation chapter
        "source": os.path.basename(rec.get("source_file") or "ipc-1860.pdf"),
        "page": rec.get("page_start"),                # citation page + dedup
        "source_type": rec.get("source_type") or "bare_act",
        "content_hash": rec.get("content_hash"),
        "structure_type": "section",
        "chunk_index": rec.get("part_index"),
        "chunk_chars": len(rec.get("embedding_text") or ""),
        "unit_type": rec.get("unit_type"),
        "act_id": rec.get("act_id"),
        "hierarchy_path": rec.get("hierarchy_path"),
        "part_index": rec.get("part_index"),
        "part_count": rec.get("part_count"),
        # act-level registry facts, propagated by step5_records.py (SPEC-silent).
        # Kept verbatim as parsed - NOT rewritten here.
        "status": rec.get("status"),
        "repealed_on": rec.get("repealed_on"),
        "replaced_by": rec.get("replaced_by"),
        "is_v2": True,
    }


def build(acts) -> dict:
    """Build CORPUS_PATH from one act or a list of acts.

    Multi-act is not just convenience: IPC and BNS have to share one index
    for the generator's IPC<->BNS comparison to be answerable, and the
    previous single-act version opened CORPUS_PATH in "w" mode - running it
    for a second act silently destroyed the first act's rows. The corpus is
    opened once after every input act has been read, and record ids are
    already act-prefixed (ipc-1860:s:302:0 / bns-2023:s:103:0), so cross-act
    id collisions are impossible and first-wins dedupe is unchanged.
    """
    if isinstance(acts, str):
        acts = [acts]
    os.makedirs(V2_OUT, exist_ok=True)
    t0 = time.time()
    log(f"seed={SEED} (deterministic build, no RNG used)")

    per_act, all_recs = {}, []
    for act in acts:
        src = os.path.join(V2_OUT, f"{act}.jsonl")
        if not os.path.isfile(src):
            raise SystemExit(f"missing v2 records: {src} (run step5_records.py)")
        with open(src, encoding="utf-8") as fh:
            recs = [json.loads(line) for line in fh if line.strip()]
        log(f"v2 records: {len(recs)} from {src}")
        per_act[act] = len(recs)
        all_recs.extend(recs)

    seen, written, empty, skipped_dup = set(), 0, 0, 0
    with open(CORPUS_PATH, "w", encoding="utf-8") as out:
        for rec in all_recs:
            rid = rec["id"]
            document = rec.get("embedding_text") or ""
            if not document.strip():
                empty += 1
                continue
            if rid in seen:
                skipped_dup += 1
                continue
            seen.add(rid)
            out.write(
                json.dumps(
                    {"id": rid, "document": document,
                     "metadata": v2_metadata(rec)},
                    ensure_ascii=False,
                )
                + "\n"
            )
            written += 1

    stats = {
        "seed": SEED,
        "acts": acts,
        "records_per_act": per_act,
        "corpus_path": CORPUS_PATH,
        "records_in": len(all_recs),
        "written": written,
        "empty_embedding_text": empty,
        "duplicate_ids": skipped_dup,
        "total_chars": sum(
            len(r.get("embedding_text") or "") for r in all_recs
        ),
        "elapsed_s": round(time.time() - t0, 1),
    }
    log("STATS " + json.dumps(stats, ensure_ascii=False))
    if empty or skipped_dup:
        log(f"FAIL: empty={empty} dup={skipped_dup}")
        return {**stats, "ok": False}
    return {**stats, "ok": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", default="ipc-1860",
                    help="act_id, or comma-separated act_ids "
                         "(e.g. ipc-1860,bns-2023)")
    args = ap.parse_args()
    acts = [a.strip() for a in args.act.split(",") if a.strip()]
    stats = build(acts)
    if not stats["ok"]:
        return 3
    log("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
