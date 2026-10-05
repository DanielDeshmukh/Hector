"""Read-only end-to-end chunk audit for HECTOR.

Reads (never writes):
  - local Chroma store: <repo>/hector_db/chroma.sqlite3, collection indian_law_bns_local
    (opened sqlite in read-only mode so nothing can be written to Chroma)
  - Pinecone index "hector-legal": describe_index_stats + list ids + one 20-id fetch
  - ingest code replay: hector/api/scripts/reingest_full.py process_pdf() (PDF read only)

Produces: record format, whole sample chunks, length stats, quality checks,
20-id id->text mapping verification, and the 17,876 vs 13,479 reconciliation.
"""

import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8",
                           errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

# This audit is long-running (full PDF replay). Ignore Ctrl+C on the shared
# console so an interrupt to the parent shell cannot truncate the log; kill by
# PID instead if a stop is needed.
try:
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)
except Exception:
    pass

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]  # <repo root>
API_DIR = ROOT / "hector" / "api"
CHROMA_SQLITE = ROOT / "hector_db" / "chroma.sqlite3"
COLLECTION_NAME = "indian_law_bns_local"
INDEX_NAME = "hector-legal"

SEED_SAMPLE = 20261001       # step 3b random chunks
SEED_BOUNDARY = 20261002     # step 3e random chunks
SEED_IDS = 20261003          # step 2 random pinecone ids

load_dotenv(ROOT / ".env")
for _p in (str(API_DIR), str(API_DIR / "scripts"), str(ROOT / "hector")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GEN_TRUNCATE = 1500  # response_generator.py:225 -> doc[:1500]


def die(label, exc):
    status = None
    for attr in ("status_code", "status", "code"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            status = v
            break
    if status is None:
        resp = getattr(exc, "response", None)
        v = getattr(resp, "status_code", None)
        if isinstance(v, int):
            status = v
    print(f"FATAL [{label}]: {type(exc).__name__}"
          + (f" HTTP status={status}" if status is not None else "")
          + f": {exc}")
    sys.exit(1)


def norm(text):
    return " ".join((text or "").lower().split())


def tok(text):
    return (text or "").split()


def pct(n, total):
    return f"{(100.0 * n / total):.2f}%" if total else "n/a"


def pctl(values, q):
    if not values:
        return 0
    idx = min(len(values) - 1, max(0, int(math.ceil(q * len(values))) - 1))
    return sorted(values)[idx]


CONTEXT_PREFIX_RE = re.compile(r"^\[[^\]\n]{0,400}\]\s*\n?")


def body_of(text):
    """Chunk text without the denormalized [Act | Chapter | Section] prefix."""
    return CONTEXT_PREFIX_RE.sub("", text or "", count=1)


def compact(meta, limit=None):
    items = list(meta.items()) if limit is None else list(meta.items())[:limit]
    return json.dumps({k: v for k, v in items}, ensure_ascii=False, default=str)


def snippet(text, width=200):
    return " ".join((text or "").split())[:width]


# --------------------------------------------------------------------------
# local store (read-only sqlite)
# --------------------------------------------------------------------------
def load_local():
    con = sqlite3.connect(f"file:{CHROMA_SQLITE}?mode=ro", uri=True)
    col_id = con.execute(
        "select id from collections where name=?", (COLLECTION_NAME,)
    ).fetchone()
    if not col_id:
        raise RuntimeError(f"collection {COLLECTION_NAME} not found in {CHROMA_SQLITE}")
    col_id = col_id[0]
    rows = con.execute(
        """
        select e.embedding_id, m.key, m.string_value, m.int_value,
               m.float_value, m.bool_value
        from embeddings e
        join embedding_metadata m on m.id = e.id
        join segments s on s.id = e.segment_id
        where s.collection = ?
        order by e.embedding_id, m.key
        """,
        (col_id,),
    ).fetchall()
    con.close()

    records = {}
    order = []
    for emb_id, key, sval, ival, fval, bval in rows:
        rec = records.get(emb_id)
        if rec is None:
            rec = {"id": emb_id, "text": "", "metadata": {}}
            records[emb_id] = rec
            order.append(emb_id)
        if key == "chroma:document":
            rec["text"] = sval or ""
            continue
        value = sval if sval is not None else (
            ival if ival is not None else (
                fval if fval is not None else bval
            )
        )
        rec["metadata"][key] = value
    return [records[i] for i in order]


def sec_of(meta):
    return str(meta.get("section_number") or meta.get("section_number_from_chunker") or "").strip()


def act_of(meta):
    return str(meta.get("real_act_name") or meta.get("act_name") or "").strip()


# --------------------------------------------------------------------------
# quality checks
# --------------------------------------------------------------------------
MARKER_RE = re.compile(
    r"\b(?:Provided\s+(?:that|also|further|nevertheless)|Explanation\.?"
    r"|Illustration(?:\s*\([a-z0-9]+\))?\s*:|Exception\s*:)",
    re.IGNORECASE,
)

ACT_PATTERNS = [
    ("IPC", re.compile(r"\b(?:Indian Penal Code|IPC)\b")),
    ("BNS", re.compile(r"\b(?:Bharatiya Nyaya Sanhita|BNS)\b")),
    ("CRPC", re.compile(r"\b(?:Code of Criminal Procedure|Cr\.?P\.?C\.?)\b", re.I)),
    ("BNSS", re.compile(r"\b(?:Bharatiya Nagarik Suraksha Sanhita|BNSS)\b")),
    ("IEA", re.compile(r"\b(?:Indian Evidence Act|Evidence Act, 1872)\b")),
    ("BSA", re.compile(r"\b(?:Bharatiya Sakshya Adhiniyam|BSA)\b")),
    ("CPC", re.compile(r"\b(?:Code of Civil Procedure|CPC)\b")),
    ("LIMITATION", re.compile(r"\bLimitation Act\b", re.I)),
    ("CONSTITUTION", re.compile(r"\b(?:Constitution of India|the Constitution)\b", re.I)),
    ("CONTRACT", re.compile(r"\bIndian Contract Act\b", re.I)),
    ("TPA", re.compile(r"\bTransfer of Property Act\b", re.I)),
    ("NIA", re.compile(r"\bNegotiable Instruments Act\b", re.I)),
    ("NDPS", re.compile(r"\bNarcotic Drugs and Psychotropic Substances Act\b", re.I)),
    ("IT", re.compile(r"\bInformation Technology Act\b", re.I)),
    ("MV", re.compile(r"\bMotor Vehicles Act\b", re.I)),
]

ACT_NAME_TO_CODE = {
    "indian penal code, 1860": "IPC",
    "bharatiya nyaya sanhita, 2023": "BNS",
    "code of criminal procedure, 1973": "CRPC",
    "bharatiya nagarik suraksha sanhita, 2023": "BNSS",
    "indian evidence act, 1872": "IEA",
    "bharatiya sakshya adhiniyam, 2023": "BSA",
    "code of civil procedure, 1908": "CPC",
    "limitation act, 1963": "LIMITATION",
    "constitution of india": "CONSTITUTION",
    "indian contract act, 1872": "CONTRACT",
    "transfer of property act, 1882": "TPA",
    "negotiable instruments act, 1881": "NIA",
    "narcotic drugs and psychotropic substances act, 1985": "NDPS",
    "information technology act, 2000": "IT",
    "motor vehicles act, 1988": "MV",
}

NOISE_PATTERNS = [
    ("standalone_page_number", re.compile(r"(?m)^\s*(?:Page\s+)?\d{1,4}\s*$")),
    ("page_x_of_y", re.compile(r"(?i)\bpage\s+\d+\s+of\s+\d+")),
    ("control_char", re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")),
    ("replacement_char", re.compile(r"\ufffd")),
    ("symbol_run_5plus", re.compile(r"[^\w\s]{5,}")),
    ("repeat_char_6plus", re.compile(r"(.)\1{5,}")),
    ("url_or_email", re.compile(r"https?://|www\.[a-z0-9]|[\w.]+@[\w.]+\.\w{2,}", re.I)),
    ("boilerplate", re.compile(r"(?i)z-library|lib\.sk|all rights reserved|downloaded from|copyright\s*[©(]")),
    ("hyphen_linebreak", re.compile(r"\w-\n\w")),
]


def check_start_mid(text):
    s = body_of(text).lstrip()
    if not s:
        return False
    return s[0].islower() or s[0] in ",;:)\].-"


def check_end_mid(text):
    s = (text or "").rstrip()
    if not s:
        return False
    return s[-1] not in ".?!"


def check_proviso_split(rec):
    b = body_of(rec["text"])
    if not MARKER_RE.search(b):
        return None
    reasons = []
    if MARKER_RE.match(b.lstrip()):
        reasons.append("chunk-starts-with-marker")
    if not sec_of(rec["metadata"]):
        if not re.search(r"Section\s+\d", b[:200], re.I):
            reasons.append("no-section-attribution")
    return ",".join(reasons) if reasons else None


def check_section_missing_from_text(rec):
    sec = sec_of(rec["metadata"])
    if not sec:
        return None
    body = body_of(rec["text"])
    if re.search(r"(?<![\w.])" + re.escape(sec) + r"(?!\d)", body):
        return None
    return f"section {sec} not in chunk body"


def check_act_mismatch(rec):
    meta = rec["metadata"]
    meta_code = ACT_NAME_TO_CODE.get(act_of(meta).lower())
    if not meta_code:
        return None
    body = rec["text"]
    found = [code for code, pat in ACT_PATTERNS if pat.search(body)]
    if meta_code in found:
        return None
    others = [c for c in found if c != meta_code]
    if not others:
        return None
    return f"metadata={meta_code} but text names {others}"


def noise_hits(text):
    hits = []
    for name, pat in NOISE_PATTERNS:
        if pat.search(text or ""):
            hits.append(name)
    return hits


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    t_run = time.perf_counter()
    api_key = os.getenv("PINECONE_API_KEY", "")
    print(f"PINECONE_API_KEY set: {'yes' if api_key else 'no'}")
    print(f"repo root: {ROOT}")
    print(f"collection: {COLLECTION_NAME}  index: {INDEX_NAME}")
    print()

    # ---------------- local store ----------------
    print("=" * 78)
    print("[1] LOCAL STORE (read-only sqlite of hector_db)")
    print("=" * 78)
    t0 = time.perf_counter()
    try:
        records = load_local()
    except Exception as exc:  # noqa: BLE001
        die("local-load", exc)
    local_ms = (time.perf_counter() - t0) * 1000
    print(f"loaded {len(records)} chunks in {local_ms:.0f} ms")

    key_counts = {}
    for rec in records:
        for k in rec["metadata"]:
            key_counts[k] = key_counts.get(k, 0) + 1
    print("\nmetadata fields (field: records present):")
    for k in sorted(key_counts, key=lambda x: (-key_counts[x], x)):
        print(f"  {k}: {key_counts[k]}")
    print("  <text field>: chroma:document -> record['text'] (all records)")

    total = len(records)

    # ---------------- 3a record format ----------------
    print()
    print("=" * 78)
    print("[2] 3a - EXACT RECORD FORMAT (one full raw example)")
    print("=" * 78)
    example = next(
        (r for r in records if sec_of(r["metadata"]) and act_of(r["metadata"])),
        records[0],
    )
    raw = {
        "id": example["id"],
        "text_field_name": "chroma:document (retrieved as record['text'])",
        "text": example["text"],
        "metadata": example["metadata"],
    }
    print("format: {id: <chroma embedding uuid>, text: str, metadata: {..all fields..}}")
    print(json.dumps(raw, indent=2, ensure_ascii=False, default=str))

    # ---------------- 3b whole samples ----------------
    print()
    print("=" * 78)
    print("[3] 3b - WHOLE CHUNKS (full text, no truncation)")
    print("=" * 78)

    def matches(act_substr, section):
        out = [
            r for r in records
            if act_substr.lower() in act_of(r["metadata"]).lower()
            and sec_of(r["metadata"]) == section
        ]
        out.sort(key=lambda r: (r["metadata"].get("page") or 0,
                                r["metadata"].get("chunk_index") or 0))
        return out

    def show_chunk(rec, note=""):
        text = rec["text"]
        print(f"\n--- chunk id={rec['id']} {note}")
        print(f"    metadata: {compact(rec['metadata'])}")
        trunc = "  [TRUNCATED BY GENERATOR]" if len(text) > GEN_TRUNCATE else ""
        print(f"    chars={len(text)} tokens={len(tok(text))} "
              f"generator_would_receive={min(len(text), GEN_TRUNCATE)}{trunc}")
        print("    ----- BEGIN WHOLE TEXT -----")
        print(text)
        print("    ----- END WHOLE TEXT -----")

    def show_selection(title, recs, max_print=4):
        print(f"\n### {title}: {len(recs)} matching chunk(s)")
        if not recs:
            print("    NOT FOUND")
            return
        for rec in recs[:max_print]:
            show_chunk(rec)
        if len(recs) > max_print:
            print(f"    ... {len(recs) - max_print} more match(es) not printed")

    bns = matches("Bharatiya Nyaya Sanhita", "103")
    show_selection("BNS section 103", bns)

    lim = matches("Limitation", "3")
    show_selection("Limitation Act 1963 section 3", lim)

    con19 = matches("Constitution", "19")
    if not con19:
        con19 = [
            r for r in records
            if "Constitution" in act_of(r["metadata"])
            and re.search(r"\bArticle\s+19\b|Section 19\b", r["text"])
        ][:4]
        note = " (found via text search for 'Article 19')"
    else:
        note = ""
    show_selection("Constitution Article/Section 19" + note, con19)

    ipc302 = matches("Indian Penal Code", "302")
    show_selection("IPC section 302", ipc302)

    longest = max(records, key=lambda r: len(r["text"]))
    show_selection("longest chunk in corpus", [longest])

    proviso = [
        r for r in records
        if MARKER_RE.search(r["text"]) and sec_of(r["metadata"])
    ]
    proviso.sort(key=lambda r: len(r["text"]))
    show_selection("a chunk containing proviso/explanation/illustration", proviso[:1])

    rng = random.Random(SEED_SAMPLE)
    picks = rng.sample(records, 5)
    print(f"\n### 5 random chunks (seed={SEED_SAMPLE})")
    for rec in picks:
        show_chunk(rec)

    # ---------------- 3c statistics ----------------
    print()
    print("=" * 78)
    print("[4] 3c - LENGTH STATISTICS OVER ALL CHUNKS")
    print("=" * 78)
    chars = [len(r["text"]) for r in records]
    words = [len(tok(r["text"])) for r in records]

    def block(name, values):
        print(f"  {name}: min={min(values)} median={pctl(values, 0.5)} "
              f"p90={pctl(values, 0.9)} max={max(values)}")

    print(f"  count={total}")
    block("characters", chars)
    block("tokens (whitespace words)", words)
    under100 = sum(1 for c in chars if c < 100)
    over2000 = sum(1 for c in chars if c > 2000)
    over1500 = sum(1 for c in chars if c > GEN_TRUNCATE)
    print(f"  under 100 chars : {under100} ({pct(under100, total)})")
    print(f"  over 2000 chars : {over2000} ({pct(over2000, total)})")
    print(f"  over {GEN_TRUNCATE} chars (generator truncates here): "
          f"{over1500} ({pct(over1500, total)})")

    # ---------------- 3d quality ----------------
    print()
    print("=" * 78)
    print("[5] 3d - QUALITY CHECKS OVER ALL CHUNKS")
    print("=" * 78)
    print("definitions:")
    print("  start_mid : body (after optional [Act|Chapter|Section] prefix) starts with")
    print("              a lowercase letter or continuation punctuation , ; : ) ] . -")
    print("  end_mid   : stored text does not end with . ? !")
    print("  proviso_* : contains Provided that/Explanation/Illustration/Exception AND")
    print("              the chunk begins with that marker or has no section attribution")
    print("  sec_missing: metadata section number never occurs as a token in the body")
    print("  act_mismatch: metadata act never named in text but another known act is")
    print("  dups      : exact = identical after lowercasing + whitespace collapse;")
    print("              near  = same first 100 normalized chars, token jaccard >= 0.9")
    print("  noise     : page numbers, page x of y, control/replacement chars, symbol")
    print("              runs, repeated chars, urls/emails, boilerplate, hyphen breaks")
    print("  missing   : field absent from metadata")

    def report(title, hits, detail_key="why"):
        print(f"\n  {title}: {len(hits)} ({pct(len(hits), total)})")
        for rec in hits[:3]:
            print(f"    id={rec['id']} meta={compact(rec['metadata'], 6)}")
            print(f"      why: {rec.get(detail_key)}")
            print(f"      text: {snippet(rec['text'], 220)}")

    hits = [dict(r, why="starts with '%s'" % body_of(r["text"]).lstrip()[:12])
            for r in records if check_start_mid(r["text"])]
    report("starts mid-sentence or mid-word", hits)

    hits = [dict(r, why="ends with '%s'" % (r["text"].rstrip()[-1] or ""))
            for r in records if check_end_mid(r["text"])]
    report("ends mid-sentence (no . ? ! terminator)", hits)

    hits = [dict(r, why=check_proviso_split(r))
            for r in records if check_proviso_split(r)]
    report("proviso/explanation/illustration separated from parent", hits)

    hits = [dict(r, why=check_section_missing_from_text(r))
            for r in records if check_section_missing_from_text(r)]
    report("section number in metadata not present in chunk text", hits)

    hits = [dict(r, why=check_act_mismatch(r))
            for r in records if check_act_mismatch(r)]
    report("act name mismatch (metadata vs act named in text)", hits)

    # duplicates
    by_norm = {}
    for r in records:
        by_norm.setdefault(norm(r["text"]), []).append(r)
    exact_groups = [g for g in by_norm.values() if len(g) > 1]
    exact_extra = sum(len(g) - 1 for g in exact_groups)
    print(f"\n  exact duplicate chunks: {exact_extra} extra copies in "
          f"{len(exact_groups)} groups ({pct(exact_extra, total)})")
    for g in exact_groups[:3]:
        print(f"    group of {len(g)}: ids={[x['id'] for x in g][:4]}")
        print(f"      text: {snippet(g[0]['text'], 180)}")

    by_prefix = {}
    for r in records:
        by_prefix.setdefault(norm(r["text"])[:100], []).append(r)
    near_pairs = []
    near_seen = set()
    for group in by_prefix.values():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if norm(a["text"]) == norm(b["text"]):
                    continue  # counted as exact
                ta, tb = set(tok(a["text"])), set(tok(b["text"]))
                if not ta or not tb:
                    continue
                jac = len(ta & tb) / len(ta | tb)
                if jac >= 0.9:
                    key = (a["id"], b["id"])
                    if key not in near_seen:
                        near_seen.add(key)
                        near_pairs.append((a, b, jac))
    print(f"\n  near-duplicate chunks (jaccard>=0.9, distinct text): "
          f"{len(near_pairs)} pairs ({pct(len(near_pairs), total)})")
    for a, b, jac in near_pairs[:3]:
        print(f"    {a['id']} <-> {b['id']} jaccard={jac:.3f}")
        print(f"      A: {snippet(a['text'], 140)}")
        print(f"      B: {snippet(b['text'], 140)}")

    noise = [(r, noise_hits(r["text"])) for r in records]
    noise = [(r, h) for r, h in noise if h]
    print(f"\n  headers/footers/page numbers/OCR noise: {len(noise)} "
          f"({pct(len(noise), total)})")
    per_pat = {}
    for r, h in noise:
        for p in h:
            per_pat[p] = per_pat.get(p, 0) + 1
    for p in sorted(per_pat, key=lambda x: -per_pat[x]):
        print(f"    {p}: {per_pat[p]} ({pct(per_pat[p], total)})")
    for r, h in noise[:3]:
        print(f"    id={r['id']} patterns={h}")
        print(f"      text: {snippet(r['text'], 200)}")

    no_page = [r for r in records if r["metadata"].get("page") is None]
    no_sec = [r for r in records if not sec_of(r["metadata"])]
    no_act = [r for r in records if not act_of(r["metadata"])]
    print(f"\n  missing 'page' field      : {len(no_page)} ({pct(len(no_page), total)})")
    print(f"  missing section fields    : {len(no_sec)} ({pct(len(no_sec), total)})")
    print(f"  missing act name          : {len(no_act)} ({pct(len(no_act), total)})")
    for title, group in (("missing section", no_sec), ("missing act", no_act)):
        for r in group[:3]:
            print(f"    {title}: id={r['id']} meta={compact(r['metadata'], 6)}")
            print(f"      text: {snippet(r['text'], 160)}")

    # ---------------- 3e boundaries ----------------
    print()
    print("=" * 78)
    print(f"[6] 3e - 25 RANDOM CHUNKS: first 200 / last 200 chars (seed={SEED_BOUNDARY})")
    print("=" * 78)
    rng = random.Random(SEED_BOUNDARY)
    for n, rec in enumerate(rng.sample(records, 25), 1):
        text = rec["text"]
        print(f"\n[{n}] id={rec['id']} chars={len(text)}")
        print(f"    metadata: {compact(rec['metadata'])}")
        print(f"    FIRST200: {text[:200]!r}")
        print(f"    LAST200 : {text[-200:]!r}")

    # ---------------- step 2: pinecone ----------------
    print()
    print("=" * 78)
    print(f"[7] STEP 2 - PINECONE '{INDEX_NAME}' + ID -> TEXT MAPPING")
    print("=" * 78)

    if not api_key:
        die("pinecone", RuntimeError("PINECONE_API_KEY not set"))

    from pinecone import Pinecone  # noqa: E402

    try:
        pc = Pinecone(api_key=api_key)
        idx = pc.Index(INDEX_NAME)
        t0 = time.perf_counter()
        stats = idx.describe_index_stats()
        pc_ms = (time.perf_counter() - t0) * 1000
    except Exception as exc:  # noqa: BLE001
        die("describe_index_stats", exc)
    if not isinstance(stats, dict):
        stats = stats.to_dict() if hasattr(stats, "to_dict") else dict(stats)
    print(f"stats: dimension={stats.get('dimension')} "
          f"total_vector_count={stats.get('total_vector_count')} "
          f"namespaces={stats.get('namespaces')} elapsed_ms={pc_ms:.0f}")

    # list all ids
    try:
        t0 = time.perf_counter()
        pc_ids = []
        for page in idx.list(limit=100):
            vecs = page.get("vectors") or []
            for v in vecs:
                pc_ids.append(getattr(v, "id", None) or
                              (v.get("id") if isinstance(v, dict) else str(v)))
        list_ms = (time.perf_counter() - t0) * 1000
    except Exception as exc:  # noqa: BLE001
        die("list_ids", exc)
    pc_id_set = set(pc_ids)
    print(f"listed ids: {len(pc_ids)} (unique {len(pc_id_set)}) "
          f"in {list_ms:.0f} ms; all 'vec_' prefixed: "
          f"{all(i.startswith('vec_') for i in pc_ids)}")

    # replay ingest to map id -> chunk record
    print("\nreplaying hector/api/scripts/reingest_full.py process_pdf() "
          "(read-only) to rebuild id -> chunk mapping ...")
    try:
        import reingest_full as RF
    except Exception as exc:  # noqa: BLE001
        die("import reingest_full", exc)

    sim_map = {}          # id -> record (last writer wins, like Pinecone upsert)
    sim_records = 0
    sim_ids_generated = 0
    replay_rows = []
    pdfs = sorted(RF.BOOKS_DIR.glob("*.pdf"))
    for pdf in pdfs:
        if pdf.name in RF.SKIP_PDFS:
            replay_rows.append((pdf.name, "SKIP_LIST", 0, 0, 0))
            continue
        if pdf.stat().st_size > 50 * 1024 * 1024:
            replay_rows.append((pdf.name, "SKIP_TOO_LARGE", 0, 0, 0))
            continue
        t0 = time.perf_counter()
        try:
            recs = RF.process_pdf(pdf)
        except Exception as exc:  # noqa: BLE001
            die(f"replay process_pdf({pdf.name})", exc)
        if not recs:
            replay_rows.append((pdf.name, "NO_RECORDS", 0, 0, time.time() - t0))
            continue
        vec_buffer, upserted, ids = [], 0, []
        for i in range(0, len(recs), RF.EMBED_BATCH):
            batch = recs[i:i + RF.EMBED_BATCH]
            for j, rec in enumerate(batch):
                sec = rec["metadata"].get("section_number", "")
                cid = hashlib.md5(
                    f"{pdf.name}_{sec}_{upserted + j}".encode()
                ).hexdigest()[:24]
                vid = f"vec_{cid}"
                ids.append(vid)
                sim_map[vid] = {
                    "id": vid,
                    "text": rec["document"],
                    "metadata": rec["metadata"],
                }
            vec_buffer.extend(batch)
            if len(vec_buffer) >= 100:
                upserted += len(vec_buffer)
                vec_buffer = []
        sim_records += len(recs)
        sim_ids_generated += len(ids)
        matched = sum(1 for v in set(ids) if v in pc_id_set)
        replay_rows.append((pdf.name, "ok", len(recs), matched, time.time() - t0))
        print(f"  replayed {pdf.name}: records={len(recs)} "
              f"ids_in_index={matched} {time.time() - t0:.1f}s", flush=True)

    print(f"\n{'pdf':60s} {'status':12s} {'recs':>6s} {'ids_in_pc':>9s} {'sec':>6s}")
    for name, status, n, matched, dt in replay_rows:
        print(f"{name[:60]:60s} {status:12s} {n:6d} {matched:9d} {dt:6.1f}")
    print(f"replayed records={sim_records} ids_generated={sim_ids_generated} "
          f"unique_sim_ids={len(sim_map)}")

    matched_ids = set(sim_map) & pc_id_set
    real_only = pc_id_set - set(sim_map)
    sim_only = set(sim_map) - pc_id_set
    print(f"\nid reconciliation:")
    print(f"  pinecone ids present in replay      : {len(matched_ids)} "
          f"({pct(len(matched_ids), len(pc_id_set))} of index)")
    print(f"  pinecone ids NOT produced by replay : {len(real_only)}")
    print(f"  replay ids missing from pinecone    : {len(sim_only)} "
          "(id collisions that overwrote, failed embed batches, or pdfs not in index)")
    for v in sorted(real_only)[:5]:
        print(f"    real-only example: {v}")
    for v in sorted(sim_only)[:5]:
        print(f"    sim-only example : {v}")

    # ---- 20 random ids verification ----
    print(f"\n20 RANDOM PINECONE IDS (seed={SEED_IDS})")
    rng = random.Random(SEED_IDS)
    sample_ids = rng.sample(sorted(pc_id_set), 20)
    try:
        t0 = time.perf_counter()
        fetched = idx.fetch(ids=sample_ids)
        fetch_ms = (time.perf_counter() - t0) * 1000
    except Exception as exc:  # noqa: BLE001
        die("fetch_20_ids", exc)
    vectors = fetched.vectors or {}
    print(f"fetched {len(vectors)}/{len(sample_ids)} vectors in {fetch_ms:.0f} ms")

    local_by_id = {r["id"] for r in records}
    local_index = {}
    for r in records:
        local_index.setdefault(
            (r["metadata"].get("source"), sec_of(r["metadata"])), []
        ).append(r)

    resolved_text_by_id = 0
    resolved_section_join = 0
    act_section_match = 0
    has_pc_text = 0
    print(f"\n{'#':>2} {'id':28} {'pc_text':7} {'id_in_local':11} {'replay':6} "
          f"{'pc_act/section':45} {'local_text_records':18} {'match'}")
    for n, vid in enumerate(sorted(vectors), 1):
        vec = vectors[vid]
        meta = vec.metadata or {}
        text_ok = bool(meta.get("document"))
        if text_ok:
            has_pc_text += 1
        in_local = vid in local_by_id
        if in_local:
            resolved_text_by_id += 1
        replay_rec = sim_map.get(vid)
        pc_source = meta.get("source")
        pc_sec = str(meta.get("section_number") or "").strip()
        pc_act = str(meta.get("real_act_name") or meta.get("act_name") or "").strip()
        join = local_index.get((pc_source, pc_sec), [])
        if join:
            resolved_section_join += 1
        match = "-"
        if join:
            acts = {act_of(r["metadata"]) for r in join}
            sec_ok = all(sec_of(r["metadata"]) == pc_sec for r in join)
            act_ok = pc_act in acts
            match = f"act={'Y' if act_ok else 'N'} sec={'Y' if sec_ok else 'N'}"
            if act_ok and sec_ok:
                act_section_match += 1
        replay_ok = "Y" if replay_rec else "N"
        if replay_rec:
            rs = str(replay_rec["metadata"].get("section_number") or "").strip()
            if rs != pc_sec:
                replay_ok = f"Y!=({rs})"
        print(f"{n:2d} {vid:28} {'Y' if text_ok else 'N':7} "
              f"{'Y' if in_local else 'N':11} {replay_ok:6} "
              f"{(str(pc_act)[:24] + '/' + pc_sec):45} {len(join):18d} {match}")
    print(f"\n  ids whose text record lives IN Pinecone (metadata['document']): "
          f"{has_pc_text}/20")
    print(f"  ids resolvable by exact id in local Chroma            : "
          f"{resolved_text_by_id}/20")
    print(f"  ids resolvable by (source, section_number) join        : "
          f"{resolved_section_join}/20")
    print(f"  ...of those, act AND section both match                : "
          f"{act_section_match}/20")

    # what the generator would receive for a Pinecone hit
    first_vec = next(iter(vectors.values()), None)
    if first_vec is not None:
        m = first_vec.metadata or {}
        doc = m.get("document", "")
        act = m.get("real_act_name") or m.get("act_name") or "Unknown"
        section = m.get("section_number") or ""
        label = f"[Source 1: {act}" + (f", Section {section}" if section else "") + "]"
        print("\ngenerator context for this Pinecone hit "
              "(response_generator.py:207-225 -> f'{label}\\n{doc[:1500]}'):")
        print("  " + label.replace("\n", "\n  "))
        print("  " + (doc[:GEN_TRUNCATE] if doc else "<EMPTY STRING - no text in metadata>"))

    # ---- count mismatch ----
    print()
    print("=" * 78)
    print("[8] COUNT MISMATCH: Pinecone vs local Chroma")
    print("=" * 78)
    pc_total = stats.get("total_vector_count")
    print(f"pinecone 'hector-legal' : total_vector_count={pc_total} "
          f"(listed ids={len(pc_id_set)})")
    print(f"local '{COLLECTION_NAME}': documents={total}")
    print(f"difference: {len(pc_id_set) - total:+d}")
    try:
        prog = json.loads((API_DIR / "scripts" / "reingest_progress.json").read_text())
        print(f"reingest_progress.json total_vectors counter: "
              f"{prog.get('total_vectors')} (upsert attempts, not unique ids)")
    except Exception as exc:  # noqa: BLE001
        print(f"reingest_progress.json unreadable: {type(exc).__name__}: {exc}")

    # which chunk texts exist in only one store (exact normalized text)
    pc_texts = {}
    for vid in matched_ids:
        rec = sim_map[vid]
        pc_texts.setdefault(norm(rec["text"]), rec)
    local_texts = {}
    for r in records:
        local_texts.setdefault(norm(r["text"]), r)

    both_texts = set(pc_texts) & set(local_texts)
    only_pc_texts = set(pc_texts) - set(local_texts)
    only_local_texts = set(local_texts) - set(pc_texts)
    print(f"\nexact normalized chunk text:")
    print(f"  unique pinecone chunk texts (from replay, ids in index): {len(pc_texts)}")
    print(f"  unique local chunk texts                               : {len(local_texts)}")
    print(f"  present in BOTH                                         : {len(both_texts)}")
    print(f"  ONLY in pinecone                                        : {len(only_pc_texts)}")
    print(f"  ONLY in local                                           : {len(only_local_texts)}")
    for t in list(sorted(only_pc_texts))[:3]:
        print(f"    only-pc ex: id={pc_texts[t]['id']} {snippet(pc_texts[t]['text'], 140)}")
    for t in list(sorted(only_local_texts))[:3]:
        print(f"    only-local ex: id={local_texts[t]['id']} {snippet(local_texts[t]['text'], 140)}")

    # (source, section) level
    def key_of(source, section):
        return (str(source or ""), str(section or "").strip())

    pc_keys = {}
    for vid in matched_ids:
        rec = sim_map[vid]
        k = key_of(rec["metadata"].get("source"),
                   rec["metadata"].get("section_number", ""))
        pc_keys.setdefault(k, []).append(vid)
    loc_keys = {}
    for r in records:
        k = key_of(r["metadata"].get("source"), sec_of(r["metadata"]))
        loc_keys.setdefault(k, []).append(r["id"])

    only_pc_keys = set(pc_keys) - set(loc_keys)
    only_loc_keys = set(loc_keys) - set(pc_keys)
    both_keys = set(pc_keys) & set(loc_keys)
    print(f"\n(source, section) groups:")
    print(f"  pinecone groups={len(pc_keys)} local groups={len(loc_keys)} "
          f"both={len(both_keys)} only_pinecone={len(only_pc_keys)} "
          f"only_local={len(only_loc_keys)}")
    for k in sorted(only_pc_keys)[:5]:
        print(f"    only-pc    : {k} ({len(pc_keys[k])} vectors)")
    for k in sorted(only_loc_keys)[:5]:
        print(f"    only-local : {k} ({len(loc_keys[k])} chunks)")

    # per-source counts
    pc_by_src = {}
    for vid in matched_ids:
        s = sim_map[vid]["metadata"].get("source") or "?"
        pc_by_src[s] = pc_by_src.get(s, 0) + 1
    loc_by_src = {}
    for r in records:
        s = r["metadata"].get("source") or "?"
        loc_by_src[s] = loc_by_src.get(s, 0) + 1
    print(f"\nper-source counts (top 15 by |diff|):")
    print(f"  {'source':62s} {'pinecone':>9s} {'local':>7s} {'diff':>7s}")
    all_src = sorted(set(pc_by_src) | set(loc_by_src),
                     key=lambda s: -abs(pc_by_src.get(s, 0) - loc_by_src.get(s, 0)))
    for s in all_src[:15]:
        a, b = pc_by_src.get(s, 0), loc_by_src.get(s, 0)
        print(f"  {s[:62]:62s} {a:9d} {b:7d} {b - a:7d}")
    only_pc_src = sorted(set(pc_by_src) - set(loc_by_src))
    only_loc_src = sorted(set(loc_by_src) - set(pc_by_src))
    print(f"  sources only in pinecone ({len(only_pc_src)}): {only_pc_src}")
    print(f"  sources only in local     ({len(only_loc_src)}): {only_loc_src}")

    # sampled containment: is the pinecone chunk text contained in some local chunk?
    rng = random.Random(SEED_IDS + 1)
    pc_recs = [sim_map[v] for v in sorted(matched_ids)]
    sample = rng.sample(pc_recs, min(200, len(pc_recs)))
    local_norm_by_src = {}
    for r in records:
        local_norm_by_src.setdefault(
            r["metadata"].get("source"), []
        ).append(norm(r["text"]))
    contained = 0
    for rec in sample:
        src = rec["metadata"].get("source")
        ntext = norm(rec["text"])
        if not ntext:
            continue
        if any(ntext in t for t in local_norm_by_src.get(src, [])):
            contained += 1
    print(f"\nsampled containment (seed={SEED_IDS + 1}): {contained}/{len(sample)} "
          "pinecone chunk texts appear verbatim inside some local chunk "
          "of the same source")

    print(f"\nDONE in {time.perf_counter() - t_run:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
