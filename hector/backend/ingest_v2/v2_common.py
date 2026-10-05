#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v2_common.py - shared helpers for the ingest_v2 pilot (new code only).

Rules: reads PDFs, writes ONLY under hector/backend/ingest_v2/.
No Pinecone/Chroma, no import of the existing chunker/ingestor.
"""

import re
import sys
import json
import hashlib
from pathlib import Path

try:
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8",
                           errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

try:
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)
except Exception:
    pass

try:
    import pymupdf as fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    print("FATAL PyMuPDF not importable:", exc, file=sys.stderr)
    raise

ROOT = Path(r"D:\Vs Code\VS code\Hector")
INGEST = ROOT / "hector" / "backend" / "ingest_v2"
SOURCES = INGEST / "sources"
RESULTS = INGEST / "results"
OUTPUT = INGEST / "output"
REGISTRY_PATH = INGEST / "act_registry.yaml"


def ensure_dirs():
    for p in (RESULTS, OUTPUT):
        p.mkdir(parents=True, exist_ok=True)


class Tee:
    """Write to the console and to a log file at the same time."""

    def __init__(self, log_path, stream):
        self._stream = stream
        self._file = open(log_path, "w", encoding="utf-8", errors="backslashreplace")

    def write(self, data):
        try:
            self._file.write(data)
            self._file.flush()
        except Exception:
            pass
        try:
            self._stream.write(data)
            self._stream.flush()
        except Exception:
            pass

    def flush(self):
        for t in (self._file, self._stream):
            try:
                t.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def tee(name):
    """Tee stdout+stderr into ingest_v2/results/<name>.log (no shell tee exists)."""
    ensure_dirs()
    log_path = RESULTS / f"{name}.log"
    sys.stdout = Tee(log_path, sys.stdout)
    sys.stderr = sys.stdout
    print(f"[tee] logging to {log_path}", flush=True)
    return log_path


def load_registry():
    import yaml
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [a for a in data["acts"]]


# ---------------------------------------------------------------- text utils
def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def squash(s):
    """Lowercase, alnum-only (spaces kept) - for fuzzy title comparison."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


PAGE_NUM_RE = re.compile(r"^\s*\d{1,4}\s*$")
SEP_CHARS = set("-=_*~#.'\u2022\u00b7\u2014\u2013")
SEP_RE = re.compile(r"^[\s" + re.escape("".join(sorted(SEP_CHARS))) + r"]+$")
BOILERPLATE_RE = re.compile(
    r"this bare act is a government source|used strictly for educational purposes",
    re.I)
FOOT_RE = re.compile(
    r"^\s*(\d{1,3})\.\s+(?:Subs\.|Substituted|Ins\.|Inserted|Omitted|Added|"
    r"Rep\.|Repealed|Amended|Deleted|Re-numbered|Renumbered|New Rule|"
    r"Subs for)(?=\s|$)",
    re.I)
WHITELIST_PREFIX = ("illustration", "illustrations", "explanation", "exception",
                    "exceptions", "provided", "chapter", "part", "schedule")
ENTRY_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*(\.*\S.*\S)\s*$")
CHAPTER_RE = re.compile(
    r"^\s*\[?\s*CHAPTER\s+([IVXLCDM]{1,8}[A-Z]?)\b\s*[-.:]?\s*(.*)$", re.I)
HYPHEN_BREAK_RE = re.compile(r"(?<=[A-Za-z])-\n(?=[a-z])")


def is_separator(line):
    s = line.strip()
    if len(s) < 4 or not s:
        return False
    if any(ch.isalnum() for ch in s):
        return False
    return all(ch in SEP_CHARS or ch.isspace() for ch in s) and \
        sum(ch in SEP_CHARS for ch in s) >= 3


def is_whitelisted(line):
    s = line.strip().lower()
    return any(s.startswith(p + " ") or s == p for p in WHITELIST_PREFIX)


# ------------------------------------------------------------ fitz helpers
def reading_order(page):
    """Return (mode, blocks sorted in reading order).

    mode is 'single-column' | 'two-column' | 'empty'.
    Evidence for the choice is printed by step2_inspect.py.
    """
    raw = page.get_text("blocks")
    bl = [b for b in raw if len(b) >= 7 and b[6] == 0 and str(b[4]).strip()]
    if not bl:
        return "empty", []
    W = page.rect.width
    mid = W / 2.0
    wide = [b for b in bl if (b[2] - b[0]) > 0.6 * W]
    left = [b for b in bl if b not in wide and b[2] <= mid + 6]
    right = [b for b in bl if b not in wide and b[0] >= mid - 6]
    other = [b for b in bl if b not in wide and b not in left and b not in right]
    if len(wide) >= 3 and len(left) + len(right) <= 2:
        mode = "single-column"

        def key(b):
            return (round(b[1], 1), round(b[0], 1))
    elif len(left) >= 2 and len(right) >= 2 and len(other) <= 1:
        mode = "two-column"

        def key(b):
            col = 0 if b[2] <= mid + 6 else (1 if b[0] >= mid - 6 else
                                             (0 if b[0] < mid else 1))
            return (col, round(b[1], 1), round(b[0], 1))
    else:
        mode = "single-column"

        def key(b):
            return (round(b[1], 1), round(b[0], 1))
    return mode, sorted(bl, key=key)


def page_lines(page):
    """Lines of a page in reading order: [{'text','y','x0','page_h'}]."""
    mode, blocks = reading_order(page)
    H = page.rect.height
    lines = []
    for b in blocks:
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
        ls = str(txt).split("\n")
        n = max(1, len(ls))
        for i, l in enumerate(ls):
            lines.append({"text": l.rstrip(),
                          "y": y0 + (y1 - y0) * (i + 0.5) / n,
                          "x0": x0, "page_h": H})
    return mode, lines


def title_score(expected_title, candidate):
    """Fuzzy score in [0,1] between ToC title and candidate marker text."""
    e = squash(expected_title)
    c = squash(candidate)
    if not e or not c:
        return 0.0
    import difflib
    window = c[:len(e) + 40]
    return difflib.SequenceMatcher(None, e, window).ratio()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[write] {path}", flush=True)


def body_scan_start(act_id):
    """0-based first page of the body scan; ONE rule shared by every step.

    ToC mode: the Arrangement/Contents window excludes the page whose entry
    numbers restart (body page), so max(toc_pages_1based) is already the
    0-based index of the first body page.  No ToC (sequence_only): 0.
    """
    p = RESULTS / f"{act_id}_toc_meta.json"
    if p.exists():
        try:
            meta = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return 0
        pages = meta.get("toc_pages_1based") or []
        if meta.get("mode") == "toc" and pages:
            return max(pages)
    return 0
