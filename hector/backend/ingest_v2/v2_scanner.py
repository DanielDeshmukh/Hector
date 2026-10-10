#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v2_scanner.py - shared forward-pass section scanner for ingest_v2.

scan_document(doc) -> dict with lines/markers/footnotes/stats/classes.
Rules per SPEC.md AMENDMENTS A1-A6. No hardcoding of numbers/titles.
"""

import re
import sys
from bisect import bisect_left, bisect_right

import v2_common as V

LOOKAHEAD_LINES = 40
DIRECT_LOOKAHEAD_LINES = 10
TITLE_CONT_LINES = 8
MISTYPE_TOLERANCE = 100

FREF_RE = re.compile(r"^\s*(?:\d{1,3}\s*)?\*+(?:\[+)?|^\s*\d{1,3}\s*\[+")
NUMHEAD_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*$")
NUMDOT_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*(.*)$")
DIRECT_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s+\S")
RESTATED_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.(?:\s+|--\s*|$)")
QUOTE_NUM_RE = re.compile(
    r"^\s*(\d{1,4}[A-Za-z]{0,2})\s+(?=[\"'\u2018\u2019\u201c\u201d\[(])")
RANGE_RE = re.compile(r"^\s*(\d{1,4})\s+to\s+(\d{1,4}[A-Za-z]{0,2})\.")
DASH_RE = re.compile(r"--|\u2013|\u2014")
TITLE_CUT_RE = re.compile(r"\.\s*[-\u2013\u2014]|--|[\u2013\u2014]")
REP_RE = re.compile(
    r"(?i:\]\s*Rep\.)|\bRep\.,?\s*(?:by\b|ibid)|(?i:\]\s*omitted\b)")
SOFT_RE = re.compile(r"[\u00ad\u200b\u200c\u200d]")
PROTECTED_RE = re.compile(r"^\s*(?:Explanation|Exception|Provided\b|Illustration)", re.I)
SPLIT_LINE_RE = re.compile(r"^\(\d+[a-z]?\)")
CHAP_HEAD_RE = re.compile(
    r"(?i:CHAPTER)\s+(?i:[IVXLCDM]){1,8}[A-Z]?"
    r"(?=\s*$|\s*[-.:]|\s*\[|\s+(?![a-z]))")
FOOT_HEAD_RE = re.compile(r"^\s*(\d{1,3})\.(?:\s|$)")
# Page-bottom amendment footnotes in some editions (IEA 1872) are plain
# "N. Cf. the General Clauses Act..." / "N. See now the Code..." lines
# with no marker glyph; by shape they are indistinguishable from section
# heads, and try_direct would accept them whenever their number is not
# yet taken (one such steal poisons last_base and the increasing rule
# then rejects every real section until the next accepted number).
# Real section titles never open with these citation verbs.
FOOTNOTE_CITE_RE = re.compile(
    r"^\s*\d{1,4}[A-Za-z]{0,2}\.\s+(?:Cf\.|See\s|The\s+Act\s+has\s+been"
    r"|Extended\s+to|The\s+words\b)", re.I)
# Title period + 2+ spaces + capital = title ends, body starts on the SAME
# line with no dash (IEA s86 prints "records.  The Court may presume...").
# Single-space periods stay out so the 4 indexed books are untouched.
SELF_BODY_RE = re.compile(r"\.\s{2,}(?=[A-Z\"'\u2018\u201c])")
INLINE_REF_RES = [
    re.compile(r"(?<!\d)(\d{1,3})\s*\*\["),
    re.compile(r"(?<!\d)(\d{1,3})\s*\*{1,4}(?!\*)"),
    # this edition: ref brackets open before letters, digits (1[40., 4[64,)
    # and curly quotes (2[“...”), not only before ASCII letters/quotes
    re.compile(r"(?<!\d)(\d{1,3})\s*\[(?=[A-Za-z0-9\"'\u201c\u2018(])"),
    # this edition: superscript markers glued to the next word with no
    # bracket at all (4Regulation VII, 5Indian Navy) - whitespace-bounded,
    # 1-2 digits, must open a Capitalized word (keeps 304A/498A safe)
    re.compile(r"(?<!\S)(\d{1,2})(?=[A-Z][a-z])"),
]


def fref_strip(s):
    prev = None
    while prev != s:
        prev = s
        s = FREF_RE.sub("", s)
    return s


def chapter_head(s):
    """Return the chapter-heading text if s is a CHAPTER heading line.

    Tolerates a reference prefix (e.g. '1*[CHAPTER XXA') and a leading '['.
    """
    if "CHAPTER" not in s.upper():
        return None
    t = fref_strip(s).lstrip()
    while t.startswith("["):
        t = t[1:].lstrip()
    if CHAP_HEAD_RE.match(t):
        return t
    return None


def num_parts(s):
    """Return (number, rest) if s starts with a section-like number, else None.

    Requires a real restated signature: number + dot (followed by whitespace,
    a dash pair, or end) OR number + whitespace + quote/bracket. This rejects
    plain prose like "125 and 126." while accepting "121.--Whoever" and
    '17 "Government"...'.
    """
    t = fref_strip(s.lstrip())
    m = RESTATED_RE.match(t)
    if m and t[m.end():].strip():
        return m.group(1), t[m.end():]
    m = QUOTE_NUM_RE.match(t)
    if m and t[m.end():].strip():
        return m.group(1), t[m.end():]
    return None


def base_of(num):
    return int(re.sub(r"[A-Za-z]+", "", num))


def suffix_of(num):
    return re.sub(r"[0-9]+", "", num)


def is_struct_line(s):
    t = s.strip()
    if chapter_head(t):
        return True
    if len(t) < 5:
        return False
    if not t.isupper():
        return False
    if not re.search(r"[A-Z]", t):
        return False
    if re.search(r"\d", t):
        return False
    return True


def classify_kind(s):
    if V.PAGE_NUM_RE.match(s):
        return "page_number"
    if V.is_separator(s):
        return "separator"
    if V.BOILERPLATE_RE.search(s):
        return "boilerplate"
    if chapter_head(s):
        return "header"
    if is_struct_line(s):
        return "header"
    return None


def _clean_title(s):
    t = SOFT_RE.sub("", s).strip()
    t = fref_strip(t)
    dm = TITLE_CUT_RE.search(t)
    if dm:
        t = t[:dm.start()]
    rm = re.search(r"(?i:\]\s*(?:Rep\.|Omitted\b))|\bRep\.,?\s*(?:by\b|ibid)",
                   t)
    if rm:
        t = t[:rm.start()]
    t = t.strip()
    if t.startswith("["):
        t = t[1:].strip()
    t = re.sub(r"^\d{1,4}[A-Za-z]{0,2}\.\s*", "", t)
    if t.startswith("["):
        t = t[1:].strip()
    t = re.sub(r"^\d{1,4}[A-Za-z]{0,2}\s+(?=[\"'\u2018\u2019\u201c\u201d])",
               "", t)
    if t.endswith("]"):
        t = t[:-1]
    t = t.strip().rstrip(".").strip()
    return t or None


def _increasing(num, last_base):
    b = base_of(num)
    suf = suffix_of(num)
    if suf:
        if b == last_base:
            return True, last_base
        return None, last_base
    if b > last_base:
        return True, b
    return None, last_base


def _strip_glue(num, last_base):
    """Undo a bare footnote-marker digit glued onto a section number.

    Some extractions lose the bracket marker entirely ("1145." for
    "1[145."). No bare act in scope reaches 1000 sections, so a 4+ digit
    head whose remaining tail continues the current run is a footnote
    marker digit, not a section number. Returns the original num when
    no strip candidate continues the run.
    """
    if not num.isdigit() or len(num) < 4:
        return num
    for cut in (1, 2):
        cand = num[cut:]
        if len(cand) >= 2 and cand.isdigit() \
                and last_base < int(cand) <= last_base + 10:
            return cand
    return num


def _title_from(first, start_j, lines):
    """Join the marker line + continuation lines until a dash, for the title."""
    if TITLE_CUT_RE.search(first):
        return _clean_title(first), start_j - 1
    parts = [first]
    j = start_j
    while j < len(lines) and len(parts) < TITLE_CONT_LINES + 1:
        s = lines[j]["text"]
        k = classify_kind(s)
        if k in ("header", "boilerplate", "page_number", "separator"):
            break
        if NUMHEAD_RE.match(s) or NUMDOT_RE.match(fref_strip(s)):
            break
        parts.append(s)
        if TITLE_CUT_RE.search(s):
            break
        j += 1
    return _clean_title(" ".join(parts)), j


def scan_document(doc, start_page=0):
    # ---- extract global lines (blank dropped; soft hyphens stripped; hyphen
    # breaks merged keeping the hyphen); start_page (0-based) excludes the
    # Arrangement/Contents pages - ONE shared rule (v2_common.body_scan_start)
    # used by every step so scans stay byte-identical ----------------------
    raw = []
    for pi in range(start_page, len(doc)):
        pg = doc[pi]
        _, ls = V.page_lines(pg)
        for l in ls:
            t = SOFT_RE.sub("", l["text"]).rstrip()
            if not t.strip():
                continue
            raw.append({"page": pi, "page_last": pi, "text": t,
                        "y": l["y"], "x0": l["x0"]})
    lines = []
    hyphen_merges = 0
    for r in raw:
        if (lines and re.search(r"[A-Za-z0-9]-$", lines[-1]["text"])
                and re.match(r"[a-z]", r["text"])):
            lines[-1]["text"] += r["text"]
            lines[-1]["page_last"] = r["page"]
            hyphen_merges += 1
            continue
        lines.append(r)
    for i, ln in enumerate(lines):
        ln["i"] = i
        ln["kind"] = classify_kind(ln["text"])
        ln["label"] = None
        ln["group"] = None
        ln["cls"] = None
    # running repeated-line rule (mirrors step6 gate_g4): a non-whitelisted
    # line >=4 chars on >=30% of scanned pages is a running header/footer
    # -> boilerplate (labeled + removed; breaks title/group continuation).
    # Data-driven: exact-text page frequency, no per-book strings.
    seen_pages = {}
    for ln in lines:
        t = ln["text"].strip()
        if t:
            seen_pages.setdefault(t, set()).add(ln["page"])
    n_scanned = max(1, len(doc) - start_page)
    repeat_lines = sorted(
        t for t, ps in seen_pages.items()
        if len(ps) / n_scanned >= 0.30 and len(t) >= 4
        and not V.is_whitelisted(t) and not V.PAGE_NUM_RE.match(t)
        and not V.is_separator(t))
    repeat_set = set(repeat_lines)
    for ln in lines:
        if ln["kind"] is None and ln["text"].strip() in repeat_set:
            ln["kind"] = "boilerplate"

    markers = []
    rejected = []
    groups = []
    open_group = None
    consumed = set()
    accepted_nums = set()
    last_base = 0
    chapter = None
    chapter_pending = None
    max_lookahead = 0
    restated_far = []

    def close_group():
        nonlocal open_group
        if open_group is not None:
            g = open_group
            g["end"] = g["members"][-1] + 1
            for gi in g["members"]:
                lines[gi]["label"] = "footnote"
                lines[gi]["group"] = g["id"]
            open_group = None

    def start_group(i):
        nonlocal open_group
        g = {"id": len(groups), "start": i, "members": [i],
             "owner": markers[-1]["id"] if markers else None}
        groups.append(g)
        open_group = g
        lines[i]["label"] = "footnote"
        lines[i]["group"] = g["id"]

    def accept(i, num, title, form, restated_idx, status_hint):
        nonlocal last_base
        b = base_of(num)
        if not suffix_of(num):
            last_base = b
        mid = len(markers)
        mk = {
            "id": mid, "number": num, "title": title, "base": b,
            "page_1based": lines[i]["page"] + 1, "line": i,
            "form": form, "restated": restated_idx,
            "status_hint": status_hint, "chapter": chapter,
            "covers": [],
        }
        accepted_nums.add(num)
        markers.append(mk)
        if restated_idx is not None:
            consumed.add(restated_idx)
            lines[restated_idx]["cls"] = "restated"
            rp = lines[restated_idx]["page"]
            mp = lines[i]["page"]
            if rp - mp > 2:
                restated_far.append({"number": num, "margin_page": mp + 1,
                                     "restated_page": rp + 1})
        return mk

    def try_margin(i):
        """Forward window from a NUMHEAD margin line. Returns marker dict or None."""
        nonlocal max_lookahead
        num = _strip_glue(NUMHEAD_RE.match(lines[i]["text"]).group(1), last_base)
        if num in accepted_nums:
            rejected.append((lines[i]["page"] + 1, lines[i]["text"][:90],
                             f"duplicate number {num} rejected (margin)"))
            return None, 0
        b = base_of(num)
        used = 0
        r_idx = None
        r_rep = None
        for j in range(i + 1, min(i + 1 + LOOKAHEAD_LINES, len(lines))):
            used = j - i
            ln = lines[j]
            if ln["kind"] in ("header", "boilerplate"):
                break
            mh = NUMHEAD_RE.match(ln["text"])
            if mh:
                if mh.group(1) == num:
                    r_idx = j
                    break
                break
            if ln["i"] in consumed:
                break
            if REP_RE.search(ln["text"]) and r_rep is None:
                r_rep = j
            np = num_parts(ln["text"])
            if np:
                if np[0] == num:
                    r_idx = j
                    break
                if (base_of(np[0]) <= b
                        and b - base_of(np[0]) <= MISTYPE_TOLERANCE):
                    r_idx = j
                    break
                break
        max_lookahead = max(max_lookahead, used)
        if r_idx is None and r_rep is None:
            return None, used
        target = r_idx if r_idx is not None else r_rep
        np = num_parts(lines[target]["text"])
        cand_num = num
        if np and np[0] == num:
            cand_num = np[0]
        ok, _ = _increasing(cand_num, last_base)
        if ok is None:
            rejected.append((lines[i]["page"] + 1, lines[i]["text"][:90],
                             f"increasing rule rejected margin {cand_num} "
                             f"(last={last_base})"))
            return None, used
        if r_idx is not None:
            if i + 1 <= r_idx - 1:
                title, end_j = _title_from(lines[i + 1]["text"], i + 2, lines)
            else:
                title, end_j = _title_from(
                    fref_strip(lines[r_idx]["text"]), r_idx + 1, lines)
            mk = accept(i, cand_num, title, "M", r_idx, "normal")
        else:
            joined = " ".join(lines[k]["text"] for k in range(i + 1, r_rep + 1))
            title = _clean_title(joined)
            mk = accept(i, cand_num, title, "R", None, "omitted")
        rp = lines[target]["page"] + 1
        mk["marker_page"] = rp
        return mk, used

    def try_direct(i):
        """Forward window from a NUMDOT line (no margin). Returns marker or None."""
        nonlocal max_lookahead
        t = fref_strip(lines[i]["text"])
        m = NUMDOT_RE.match(t)
        if m:
            num = m.group(1)
        else:
            np = num_parts(t)
            if not np:
                return None, 0
            num = np[0]
        if FOOTNOTE_CITE_RE.match(t):
            rejected.append((lines[i]["page"] + 1, t[:90],
                             f"citation-verb footnote {num} rejected (direct)"))
            return None, 0
        if V.FOOT_RE.match(t):
            # amendment footnote (N. Subs./Ins./Rep. ...) - a free number +
            # dash would otherwise let try_direct steal it as a real section
            # (IEA's page-bottom "4. Subs. by Act 21 of 2000..." shadowed the
            # real s4 on the next page).
            rejected.append((lines[i]["page"] + 1, t[:90],
                             f"amendment footnote {num} rejected (direct)"))
            return None, 0
        num = _strip_glue(num, last_base)
        if m is not None and num != m.group(1) \
                and lines[i]["text"].lstrip().startswith(m.group(1) + "."):
            # normalize the glued marker digit in the LINE TEXT too, so the
            # record text (and G3's starts-with-own-number) sees the
            # canonical number ("1145. Cross-..." -> "145. Cross-...")
            lt = lines[i]["text"]
            k = lt.index(m.group(1) + ".")
            lines[i]["text"] = lt[:k] + num + lt[k + len(m.group(1)):]
        if num in accepted_nums:
            rejected.append((lines[i]["page"] + 1, t[:90],
                             f"duplicate number {num} rejected (direct)"))
            return None, 0
        used = 0
        dash_j = None
        rep_j = None
        for j in range(i, min(i + 1 + DIRECT_LOOKAHEAD_LINES, len(lines))):
            used = j - i
            ln = lines[j]
            if j > i:
                if ln["kind"] in ("header", "boilerplate"):
                    break
                if NUMHEAD_RE.match(ln["text"]):
                    break
                if ln["i"] in consumed:
                    break
            if j > i and NUMDOT_RE.match(fref_strip(ln["text"])):
                np2 = num_parts(ln["text"])
                if np2 and np2[0] != num:
                    break
            if DASH_RE.search(ln["text"]):
                dash_j = j
                break
            if j == i and SELF_BODY_RE.search(ln["text"]):
                # no dash, but the title sentence ends and body starts on
                # the marker line itself - accept as a self-contained head
                dash_j = j
                break
            if REP_RE.search(ln["text"]):
                rep_j = j
                break
        max_lookahead = max(max_lookahead, used)
        if dash_j is None and rep_j is None:
            return None, used
        ok, _ = _increasing(num, last_base)
        if ok is None:
            rejected.append((lines[i]["page"] + 1, t[:90],
                             f"increasing rule rejected direct {num} "
                             f"(last={last_base})"))
            return None, used
        if dash_j is not None:
            title, _ = _title_from(t, i + 1, lines)
            mb = SELF_BODY_RE.search(title)
            if mb:
                title = title[: mb.start()].strip()
            return accept(i, num, title, "D", i, "normal"), used
        joined = " ".join(lines[k]["text"] for k in range(i, rep_j + 1))
        title = _clean_title(joined)
        return accept(i, num, title, "R", None, "omitted"), used

    def try_range(i, m):
        """Marker for a printed range line, e.g. '161 to 165A.Rep. ...'."""
        nonlocal last_base
        b1 = int(m.group(1))
        b2 = base_of(m.group(2))
        if b1 <= last_base:
            rejected.append((lines[i]["page"] + 1, lines[i]["text"][:90],
                             f"increasing rule rejected range {b1} "
                             f"(last={last_base})"))
            return None, 0
        num = f"{m.group(1)} to {m.group(2)}"
        covers = list(range(b1, b2 + 1))
        mk = {
            "id": len(markers), "number": num, "title": None, "base": b1,
            "page_1based": lines[i]["page"] + 1, "line": i,
            "form": "R", "restated": None,
            "status_hint": "omitted", "chapter": chapter,
            "covers": covers, "marker_page": lines[i]["page"] + 1,
        }
        markers.append(mk)
        last_base = b2
        accepted_nums.update(str(c) for c in covers)
        accepted_nums.add(num)
        accepted_nums.add(m.group(2))
        return mk, 0

    # ---- forward pass ------------------------------------------------------
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln["text"]
        st = ln["kind"]
        if ln["i"] in consumed:
            i += 1
            continue
        if st in ("page_number", "separator", "boilerplate"):
            if open_group is not None:
                close_group()
            ln["label"] = st
            i += 1
            continue
        if st == "header":
            if open_group is not None:
                close_group()
            ln["label"] = "header"
            ch_txt = chapter_head(s)
            if ch_txt:
                chapter = ch_txt.rstrip()
                chapter_pending = True
            elif chapter_pending and len(s.strip()) >= 5 and s.strip().isupper():
                if not chapter.endswith(s.strip()):
                    chapter = (chapter or "") + " - " + s.strip()
                chapter_pending = False
            else:
                chapter_pending = None
            i += 1
            continue
        if NUMHEAD_RE.match(s):
            mk, used = try_margin(i)
            if mk is not None:
                if open_group is not None:
                    close_group()
                ln["cls"] = "margin"
                chapter_pending = None
                i += 1
                continue
            if open_group is None:
                start_group(i)
                ln["cls"] = "footnote"
            else:
                s2 = open_group
                s2["members"].append(i)
                ln["label"] = "footnote"
                ln["group"] = s2["id"]
                ln["cls"] = "footnote"
            i += 1
            continue
        rng = RANGE_RE.match(fref_strip(s))
        if rng:
            mk, used = try_range(i, rng)
            if mk is not None:
                if open_group is not None:
                    close_group()
                ln["cls"] = "margin"
                chapter_pending = None
                i += 1
                continue
        st2 = fref_strip(s)
        if NUMDOT_RE.match(st2) or DIRECT_RE.match(st2) \
                or QUOTE_NUM_RE.match(st2):
            mk, used = try_direct(i)
            if mk is not None:
                if open_group is not None:
                    close_group()
                ln["cls"] = "restated" if mk["form"] in ("M", "D") else "restated"
                chapter_pending = None
                i += 1
                continue
            if open_group is not None:
                open_group["members"].append(i)
                ln["label"] = "footnote"
                ln["group"] = open_group["id"]
                ln["cls"] = "footnote"
            else:
                # open a footnote group only for a rejected number line that
                # looks like the page-number restart ("1. ...") or matches the
                # amendment/bracket footnote shapes; other rejected numbers
                # are restated section content (e.g. a "382B. Whoever ..." line
                # after its own marker) and must stay in the record text.
                m1 = NUMDOT_RE.match(st2)
                if (m1 and m1.group(1) == "1") or V.FOOT_RE.match(s) \
                        or FREF_RE.match(s.lstrip()) or REP_RE.search(s) \
                        or FOOTNOTE_CITE_RE.match(st2):
                    start_group(i)
                    ln["cls"] = "footnote"
                else:
                    ln["cls"] = "UNKNOWN"
            i += 1
            continue
        if open_group is not None:
            open_group["members"].append(i)
            ln["label"] = "footnote"
            ln["group"] = open_group["id"]
        i += 1
    close_group()

    # spans: [marker.line, next.marker.line)
    for k, mk in enumerate(markers):
        nxt = markers[k + 1]["line"] if k + 1 < len(markers) else len(lines)
        mk["start"] = mk["line"]
        mk["end"] = nxt
    first_start = markers[0]["line"] if markers else len(lines)
    for ln in lines[:first_start]:
        if ln["label"] is None:
            ln["label"] = "header"

    # heading-region Rep/omitted check -> section is removed by amendment
    for k_m, mk in enumerate(markers):
        if mk["form"] in ("M", "D"):
            anchor = mk["restated"] if mk["restated"] is not None else mk["line"]
            nxt = markers[k_m + 1]["line"] if k_m + 1 < len(markers) else len(lines)
            for k in range(mk["line"], min(anchor + 7, nxt)):
                if lines[k]["label"] is None and REP_RE.search(lines[k]["text"]):
                    mk["form"] = "R"
                    mk["status_hint"] = "omitted"
                    break

    # ---- A7b/A7c: scope boundaries, inline refs, multi-owner attachment --
    scope_boundaries = [ln["i"] for ln in lines if ln["kind"] == "page_number"]
    refs = []
    seen_refs = set()
    for ln in lines:
        is_chap = bool(chapter_head(ln["text"]))
        if ln["label"] is not None and not is_chap:
            continue
        for rx in INLINE_REF_RES:
            for m in rx.finditer(ln["text"]):
                n = int(m.group(1))
                key = (ln["i"], n)
                if key in seen_refs:
                    continue
                seen_refs.add(key)
                refs.append({"line": ln["i"], "num": n, "text": m.group(0),
                             "pos": m.start(), "chapter": is_chap})

    def span_of(group_start):
        lo_i = bisect_left(scope_boundaries, group_start) - 1
        lo = scope_boundaries[lo_i] if lo_i >= 0 else -1
        hi_i = bisect_right(scope_boundaries, group_start)
        hi = (scope_boundaries[hi_i] if hi_i < len(scope_boundaries)
              else len(lines))
        return lo, hi

    def owner_ids(r):
        """(marker ids, is_chapter_note, orphan) for one inline reference."""
        if r["chapter"]:
            for mk in markers:
                if mk["line"] > r["line"]:
                    return [mk["id"]], True, False
            return [], True, True
        for mk in markers:
            if mk["start"] <= r["line"] < mk["end"]:
                return [mk["id"]], False, False
        return [], False, True

    footnotes_out = []
    chapter_notes = []
    attached_f = una_f = amb_f = 0
    for g in groups:
        lo, hi = span_of(g["start"])
        span_refs = [r for r in refs if lo < r["line"] < hi]
        fns = []
        cur = None
        for mi in g["members"]:
            fm = FOOT_HEAD_RE.match(lines[mi]["text"])
            if fm:
                if cur is not None:
                    fns.append(cur)
                cur = {"num": fm.group(1), "members": [mi]}
            elif cur is None:
                cur = {"num": None, "members": [mi]}
            else:
                cur["members"].append(mi)
        if cur is not None:
            fns.append(cur)
        for fn in fns:
            text = "\n".join(lines[mi]["text"] for mi in fn["members"])
            entry = {
                "group": g["id"], "num": fn["num"], "members": fn["members"],
                "text": text, "span": [lo, hi],
                "pdf_page": lines[fn["members"][0]]["page"] + 1,
                "owners": [], "owner_numbers": [], "refs": [],
                "status": "", "reason": "",
            }
            n = int(fn["num"]) if fn["num"] else None
            cands = [r for r in span_refs if n is not None and r["num"] == n]
            if n is None:
                entry["status"] = "ambiguous"
                entry["reason"] = "unparseable footnote number"
                amb_f += 1
            elif not cands:
                entry["status"] = "unattached"
                entry["reason"] = f"no inline {n} reference inside span"
                una_f += 1
            else:
                owners_all = []
                orphan = False
                chap = False
                for r in cands:
                    oids, is_chap, orph = owner_ids(r)
                    t = lines[r["line"]]["text"]
                    entry["refs"].append({
                        "line": r["line"], "num": r["num"], "text": r["text"],
                        "ctx": t[max(0, r["pos"] - 40): r["pos"] + 40],
                        "owners": oids, "chapter_note": is_chap,
                    })
                    chap = chap or is_chap
                    orphan = orphan or orph
                    for oid in oids:
                        if oid not in owners_all:
                            owners_all.append(oid)
                if owners_all:
                    entry["status"] = "attached"
                    entry["owners"] = owners_all
                    entry["owner_numbers"] = [markers[oid]["number"]
                                              for oid in owners_all]
                    reasons = []
                    if orphan:
                        reasons.append("some refs outside any section span")
                    if chap:
                        reasons.append("chapter note")
                    entry["reason"] = "; ".join(reasons)
                    attached_f += 1
                elif orphan:
                    entry["status"] = "ambiguous"
                    entry["reason"] = "reference line outside any section span"
                    amb_f += 1
                else:
                    entry["status"] = "unattached"
                    entry["reason"] = "refs have no owning section marker"
                    una_f += 1
            footnotes_out.append(entry)
            if any(rr["chapter_note"] for rr in entry["refs"]):
                chapter_notes.append(entry)

    for mk in markers:
        mk["footnote_texts"] = []
    for entry in footnotes_out:
        for oid in entry["owners"]:
            markers[oid]["footnote_texts"].append(entry["text"])
    fn_by_group = {}
    for entry in footnotes_out:
        fn_by_group.setdefault(entry["group"], []).append(entry)
    for g in groups:
        own = None
        for entry in fn_by_group.get(g["id"], []):
            if entry["owners"]:
                own = entry["owners"][0]
                break
        g["owner"] = own
    attached = len(groups) - sum(1 for g in groups if g["owner"] is None)
    unattached = sum(1 for g in groups if g["owner"] is None)

    # labels / classes stats
    label_counts = {}
    class_counts = {}
    removed_sample_pool = []
    footnote_class_pool = []
    unknowns = []
    for ln in lines:
        if ln["label"]:
            label_counts[ln["label"]] = label_counts.get(ln["label"], 0) + 1
            removed_sample_pool.append(ln["i"])
        c = ln["cls"]
        if c:
            class_counts[c] = class_counts.get(c, 0) + 1
        if NUMDOT_RE.match(ln["text"]) or NUMHEAD_RE.match(ln["text"]):
            if c == "footnote":
                footnote_class_pool.append(ln["i"])
            elif c == "UNKNOWN":
                unknowns.append({"line": ln["i"], "page": ln["page"] + 1,
                                 "text": ln["text"][:120],
                                 "context": [lines[k]["text"][:100]
                                             for k in range(max(0, ln["i"] - 2),
                                                            min(len(lines), ln["i"] + 3))]})
    kept_total = sum(1 for ln in lines if ln["label"] is None)
    unlabeled_removed = (len(lines) - kept_total - sum(label_counts.values()))

    covered = set()
    for mk in markers:
        if mk.get("covers"):
            covered.update(mk["covers"])
        elif not suffix_of(mk["number"]):
            covered.add(base_of(mk["number"]))
    gaps = []
    if covered:
        lo, hi = min(covered), max(covered)
        gaps = [n for n in range(lo, hi + 1) if n not in covered]

    stats = {
        "markers": len(markers),
        "forms": {f: sum(1 for m in markers if m["form"] == f)
                  for f in ("M", "D", "R")},
        "lookahead_constant": LOOKAHEAD_LINES,
        "max_lookahead_used": max_lookahead,
        "restated_more_than_2_pages": restated_far,
        "labels": label_counts,
        "classes": class_counts,
        "unlabeled_removed": unlabeled_removed,
        "hyphen_merges": hyphen_merges,
        "footnotes_total": len(footnotes_out),
        "footnotes_attached": attached_f,
        "footnotes_unattached": una_f,
        "footnotes_ambiguous": amb_f,
        "scope_boundaries": len(scope_boundaries),
        "chapter_notes": len(chapter_notes),
        "gaps": gaps,
        "lettered": [m["number"] for m in markers if suffix_of(m["number"])],
        "rejected": len(rejected),
        "lines": len(lines),
    }
    return {"lines": lines, "markers": markers, "groups": groups,
            "stats": stats, "unknowns": unknowns,
            "repeat_lines": repeat_lines,
            "removed_pool": removed_sample_pool,
            "footnote_pool": footnote_class_pool,
            "footnotes": footnotes_out,
            "scope_boundaries": scope_boundaries,
            "chapter_notes": chapter_notes,
            "rejected": rejected}


def assemble_text(lines, idxs):
    """Join kept lines; split at join points (non-adjacent gaps).

    Returns (text, fragments, page_start_1based, page_end_1based).
    """
    if not idxs:
        return "", [], None, None
    frags = []
    cur = []
    prev = None
    for k in idxs:
        if prev is not None and k != prev + 1:
            frags.append(cur)
            cur = []
        cur.append(k)
        prev = k
    if cur:
        frags.append(cur)
    frag_texts = []
    for fr in frags:
        out = ""
        for n, gi in enumerate(fr):
            t = lines[gi]["text"]
            if n == 0:
                out = t
            elif re.search(r"[A-Za-z0-9]-$", out) and re.match(r"[a-z]", t):
                out += t
            else:
                out += "\n" + t
        frag_texts.append(out)
    text = ""
    for n, ft in enumerate(frag_texts):
        if n == 0:
            text = ft
        elif re.search(r"[A-Za-z0-9]-$", text) and re.match(r"[a-z]", ft):
            text += ft
        else:
            text += "\n" + ft
    p0 = lines[idxs[0]]["page"] + 1
    p1 = lines[idxs[-1]]["page_last"] + 1
    return text, frag_texts, p0, p1


def raw_norm_text(doc, p0, p1):
    """Whitespace-normalized raw text of pages p0..p1 (1-based, inclusive)."""
    parts = []
    for pi in range(max(0, p0 - 1), min(len(doc), p1)):
        parts.append(doc[pi].get_text("text"))
    t = "\n".join(parts)
    t = SOFT_RE.sub("", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{2,}", "\n", t)
    t = re.sub(r"\n[ \t]+", "\n", t)
    t = re.sub(r"(?<=[A-Za-z0-9])-\n(?=[a-z])", "-", t)
    return V.norm_ws(t)
