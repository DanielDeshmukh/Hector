"""Audit core/mapping.json accuracy against the ingested corpus.

Checks (no hardcoded section pairs drive anything - all findings are data-
derived, sample seed is printed):
  A. structure: duplicate raw keys, empty targets, count vs SYSTEM_NOTES
  B. name consistency: does each entry's "name" overlap the corpus title
     of its IPC side / BNS side?
  C. duplicate-target resolution: for the 111 shared BNS targets, which IPC
     does the production title-overlap tie-break pick, and does the pick
     have ANY title overlap (flag zero-overlap picks = ambiguous)
  D. coverage: corpus sections absent from the crosswalk (informational)
  E. seeded random sample for external verification (official sources)

Usage: python audit_mapping_accuracy.py [--sample 20] [--seed 20261005]
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]  # .../Hector (eval -> backend -> hector -> root)
MAPPING_PATH = ROOT / "hector" / "api" / "core" / "mapping.json"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(title: str) -> set:
    return {t for t in _TOKEN_RE.findall(str(title or "").lower()) if len(t) >= 3}


def load_corpus_titles() -> dict[tuple[str, str], str]:
    """{(act, section): section_title} from the PRODUCTION Pinecone index.

    The app serves the 945-record `hector` index (see refresh_index:
    records come from Pinecone; the local hector_db chroma is a stale
    13k legacy store). Act comes from the vector id prefix (ipc-1860 /
    bns-2023) so it never depends on metadata drift.
    """
    import os

    from dotenv import load_dotenv
    from pinecone import Pinecone

    load_dotenv(ROOT / ".env")
    index_name = os.getenv("HECTOR_EVAL_INDEX", "hector")
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    idx = pc.Index(index_name)
    titles: dict[tuple[str, str], str] = {}
    total = 0
    for resp in idx.list():
        ids = [item.id for item in (getattr(resp, "vectors", None) or [])]
        if not ids:
            continue
        fetched = idx.fetch(ids=ids)
        for vid, vec in (fetched.vectors or {}).items():
            total += 1
            meta = vec.metadata or {}
            section = meta.get("section_number") or meta.get("section")
            if not section:
                parts = str(vid).split(":")
                if len(parts) >= 3 and parts[1] == "s":
                    section = parts[2]
            title = meta.get("section_title") or meta.get("section_title_from_chunker")
            if not section or not title:
                continue
            prefix = str(vid).lower()
            if prefix.startswith("ipc"):
                act = "IPC"
            elif prefix.startswith("bns-"):
                act = "BNS"
            else:
                continue
            key = (act, str(section).strip().upper().replace(" ", ""))
            titles.setdefault(key, str(title))
    print(f"pinecone index={index_name} vectors seen={total} titled sections={len(titles)}")
    return titles


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20261005)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raw_text = MAPPING_PATH.read_text(encoding="utf-8")

    # A. structure -------------------------------------------------------
    dup_keys: list[str] = []

    def _pairs_hook(pairs):
        seen = set()
        for key, _value in pairs:
            if key in seen:
                dup_keys.append(key)
            seen.add(key)
        return dict(pairs)

    mapping = json.loads(raw_text, object_pairs_hook=_pairs_hook)
    ipc_to_bns = mapping.get("IPC_TO_BNS") or {}
    notes = mapping.get("SYSTEM_NOTES") or {}
    empty_targets = [k for k, v in ipc_to_bns.items() if not (v or {}).get("new")]
    print("== A. structure ==")
    print(f"entries: {len(ipc_to_bns)}")
    print(f"duplicate raw keys: {len(dup_keys)} {dup_keys[:5]}")
    print(f"empty targets: {len(empty_targets)} {empty_targets[:5]}")
    print(
        f"SYSTEM_NOTES.total_mapped: {notes.get('total_mapped')} "
        f"(file has {len(ipc_to_bns)})"
    )

    titles = load_corpus_titles()
    ipc_titles = {k[1]: v for k, v in titles.items() if k[0] == "IPC"}
    bns_titles = {k[1]: v for k, v in titles.items() if k[0] == "BNS"}
    print(f"corpus titles: IPC={len(ipc_titles)} BNS={len(bns_titles)}")

    # B. name consistency ------------------------------------------------
    print("\n== B. entry name vs corpus titles ==")
    classes = collections.Counter()
    suspicious: list[tuple[str, str, str, str]] = []
    for old, info in sorted(ipc_to_bns.items(), key=lambda kv: str(kv[0])):
        target = str((info or {}).get("new") or "").strip().upper()
        name = str((info or {}).get("name") or "")
        if not target or not name:
            classes["no-name"] += 1
            continue
        ipc_title = ipc_titles.get(str(old).strip().upper().replace(" ", ""))
        bns_title = bns_titles.get(target)
        name_toks = _tokens(name)
        ipc_hit = bool(name_toks & _tokens(ipc_title))
        bns_hit = bool(name_toks & _tokens(bns_title))
        if ipc_hit and bns_hit:
            classes["matches-both"] += 1
        elif ipc_hit:
            classes["matches-ipc-only"] += 1
        elif bns_hit:
            classes["matches-bns-only"] += 1
        else:
            classes["matches-neither"] += 1
            suspicious.append((str(old), target, name, bns_title or ""))
    for key in sorted(classes):
        print(f"  {key}: {classes[key]}")
    print(f"  suspicious (name matches neither corpus title): {len(suspicious)}")
    for row in suspicious[:15]:
        print(f"    IPC {row[0]} -> BNS {row[1]} | name={row[2]!r} | bns_title={row[3]!r}")

    # C. duplicate-target resolution ------------------------------------
    print("\n== C. shared-target resolution (production tie-break) ==")
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for old, info in ipc_to_bns.items():
        target = str((info or {}).get("new") or "").strip().upper()
        if target:
            groups[target].append(str(old))
    shared = {t: olds for t, olds in groups.items() if len(olds) > 1}
    print(f"shared targets: {len(shared)} (covering {sum(len(v) for v in shared.values())} entries)")
    zero_overlap: list[tuple[str, list[str], str]] = []
    for target in sorted(shared):
        target_tokens = _tokens(bns_titles.get(target, ""))
        best_section, best_score = None, -1
        for old in shared[target]:
            score = len(target_tokens & _tokens(ipc_titles.get(old, "")))
            if score > best_score:
                best_section, best_score = old, score
        if best_score <= 0:
            zero_overlap.append((target, shared[target], bns_titles.get(target, "")))
    print(f"chosen counterpart with ZERO title overlap: {len(zero_overlap)}")
    for target, olds, title in zero_overlap[:15]:
        print(f"    BNS {target} ({title!r}) <- candidates {olds}")

    # D. coverage ---------------------------------------------------------
    print("\n== D. corpus coverage (informational) ==")
    mapped_ipc = {str(k).strip().upper().replace(" ", "") for k in ipc_to_bns}
    mapped_targets = set(groups)
    ipc_in_corpus = set(ipc_titles)
    bns_in_corpus = set(bns_titles)
    print(f"IPC corpus sections with no mapping entry: {len(ipc_in_corpus - mapped_ipc)}")
    print(f"IPC mapping entries absent from corpus: {len(mapped_ipc - ipc_in_corpus)}")
    print(f"BNS corpus sections never a mapping target: {len(bns_in_corpus - mapped_targets)}")
    print(f"mapping targets absent from corpus: {len(mapped_targets - bns_in_corpus)}")

    # E. seeded sample for external verification --------------------------
    print("\n== E. external spot-check sample ==")
    print(f"seed: {args.seed}  sample size: {args.sample}")
    rng = random.Random(args.seed)
    keys = sorted(ipc_to_bns)
    for old in rng.sample(keys, min(args.sample, len(keys))):
        info = ipc_to_bns[old]
        target = str((info or {}).get("new") or "")
        print(f"  IPC {old} -> BNS {target} | name={info.get('name')!r}")

    total_flags = len(suspicious) + len(zero_overlap) + len(dup_keys) + len(empty_targets)
    print(f"\nTOTAL FLAGGED: {total_flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
