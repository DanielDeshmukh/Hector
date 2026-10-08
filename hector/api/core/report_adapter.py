"""Map a SearchResponse dict to the HECTOR report template payload."""

import re
from datetime import UTC, datetime

_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
_SEP_CELL_RE = re.compile(r"^:?-+:?$")
_SOURCE_MARK_RE = re.compile(r"\s*\[(?:Source\s*|S\s*|§\s*)(\d+)\]\s*")
_DIRECT_LABEL_RE = re.compile(r"^\s*\*\*\s*Direct\s*Answer\s*:?\s*\*\*\s*:?", re.IGNORECASE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s*")
_SOURCES_TAG_RE = re.compile(r"\s*\[Sources?[\s\d,]*\]")
_HECTOR_HEADER_RE = re.compile(r"^\s*\[HECTOR\s+Intelligence\s+Report\]", re.IGNORECASE)


def _strip_inline(text: str) -> str:
    text = _BOLD_RE.sub(r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = text.replace("`", "")
    text = _HEADING_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _split_cells(line: str) -> list[str]:
    inner = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in inner.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_SEP_CELL_RE.match(cell) for cell in cells)


def _tables_in(body: str) -> list[tuple[list[str], list[list[str]]]]:
    tables = []
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in str(body or "").split("\n"):
        if not _TABLE_LINE_RE.match(line):
            if header is not None:
                tables.append((header, rows))
                header, rows = None, []
            continue
        cells = _split_cells(line)
        if not any(cells):
            continue
        if _is_separator(cells):
            continue
        if header is None:
            header = cells
        else:
            rows.append(cells)
    if header is not None:
        tables.append((header, rows))
    return tables


def _classify(header: list[str]) -> str | None:
    lowered = [cell.lower() for cell in header]
    joined = " ".join(lowered)
    if "comparison" in joined or ("ipc" in joined and "bns" in joined):
        return "comparison"
    if any(cell in ("text", "quote", "provision", "code", "section") for cell in lowered):
        return "statutory"
    return None


def _column_index(header: list[str], names: tuple[str, ...]) -> int | None:
    for i, cell in enumerate(header):
        if cell.strip().lower() in names:
            return i
    return None


def _pull_source(text: str) -> tuple[str, int | None]:
    matches = list(_SOURCE_MARK_RE.finditer(text))
    if not matches:
        return text.strip(), None
    source = int(matches[-1].group(1))
    cleaned = _SOURCE_MARK_RE.sub("", text).strip()
    return cleaned, source


def _statutory_rows(tables) -> list[dict]:
    rows = []
    for header, body_rows in tables:
        if _classify(header) != "statutory":
            continue
        code_i = _column_index(header, ("code", "act"))
        section_i = _column_index(header, ("section",))
        provision_i = _column_index(header, ("provision",))
        text_i = _column_index(header, ("text", "quote"))
        for cells in body_rows:
            if text_i is not None and text_i < len(cells):
                text, source = _pull_source(cells[text_i])
            else:
                text, source = _pull_source(cells[-1])
            if provision_i is not None and provision_i < len(cells):
                provision = cells[provision_i]
            elif code_i is not None and code_i < len(cells):
                provision = cells[code_i]
                if section_i is not None and section_i < len(cells) and cells[section_i]:
                    provision = f"{provision} Section {cells[section_i]}"
            elif section_i is not None and section_i < len(cells):
                provision = f"Section {cells[section_i]}"
            else:
                provision = cells[0] if cells else ""
            if not provision and not text:
                continue
            rows.append({"provision": _strip_inline(provision), "source": source, "text": text})
    return rows


def _comparison_rows_from_tables(tables) -> list[dict]:
    rows = []
    for header, body_rows in tables:
        if _classify(header) != "comparison":
            continue
        ipc_i = bns_i = point_i = None
        for i, cell in enumerate(header):
            lowered = cell.strip().lower()
            if lowered.startswith("ipc") and ipc_i is None:
                ipc_i = i
            elif lowered.startswith("bns") and bns_i is None:
                bns_i = i
        if ipc_i is None:
            ipc_i = _column_index(header, ("ipc", "indian penal code, 1860 [ipc]"))
        if bns_i is None:
            bns_i = _column_index(header, ("bns", "bharatiya nyaya sanhita, 2023 [bns]"))
        if ipc_i is None and bns_i is None:
            ipc_i = 1 if len(header) > 1 else None
            bns_i = 2 if len(header) > 2 else None
        elif ipc_i is None:
            ipc_i = next((i for i in range(len(header)) if i not in (bns_i, 0)), 1)
        elif bns_i is None:
            bns_i = next((i for i in range(len(header)) if i not in (ipc_i, 0)), 2)
        for i in range(len(header)):
            if i not in (ipc_i, bns_i):
                point_i = i
                break
        if point_i is None:
            point_i = 0
        for cells in body_rows:
            def cell_at(i):
                if i is None or i >= len(cells):
                    return "", None
                return _pull_source(cells[i])
            point = cells[point_i] if point_i < len(cells) else ""
            ipc_text, ipc_source = cell_at(ipc_i)
            bns_text, bns_source = cell_at(bns_i)
            if not any((point, ipc_text, bns_text)):
                continue
            rows.append({
                "point": _strip_inline(point),
                "ipc": ipc_text,
                "ipc_source": ipc_source,
                "bns": bns_text,
                "bns_source": bns_source,
            })
    return rows


def _comparison_rows_from_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        point = row.get("point") or row.get("aspect") or ""
        ipc = row.get("ipc") or row.get("requested") or ""
        bns = row.get("bns") or row.get("counterpart") or ""
        if not any((point, ipc, bns)):
            continue
        ipc_text, ipc_source = _pull_source(str(ipc))
        bns_text, bns_source = _pull_source(str(bns))
        if row.get("ipc_source") not in (None, ""):
            ipc_source = row.get("ipc_source")
            ipc_text = str(ipc)
        if row.get("bns_source") not in (None, ""):
            bns_source = row.get("bns_source")
            bns_text = str(bns)
        out.append({
            "point": _strip_inline(point),
            "ipc": ipc_text,
            "ipc_source": ipc_source,
            "bns": bns_text,
            "bns_source": bns_source,
        })
    return out


def _direct_answer(sections: list[dict], full_answer: str) -> str:
    body = ""
    if sections and isinstance(sections[0], dict):
        body = str(sections[0].get("body") or "")
    if not body:
        body = str(full_answer or "")
    lines = [line for line in body.split("\n") if not _TABLE_LINE_RE.match(line)]
    text = "\n".join(lines)
    label = _DIRECT_LABEL_RE.search(text)
    if label:
        remainder = text[label.end():]
        para = re.split(r"\n\s*\n", remainder, maxsplit=1)[0]
        para = re.sub(r"\n(?!\s*$)", " ", para)
        cleaned = _strip_inline(para)
        if cleaned:
            return cleaned
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    for para in paragraphs:
        first_line = para.strip().split("\n")[0]
        if _HECTOR_HEADER_RE.match(first_line):
            continue
        cleaned = _strip_inline(para)
        if cleaned:
            return cleaned
    return _strip_inline(full_answer)


def _clean_difference(text: str) -> str:
    text = _SOURCE_MARK_RE.sub("", text)
    text = _SOURCES_TAG_RE.sub(" ", text)
    return text.strip(" :-–—*")


def _key_differences(sections: list[dict]) -> list[str]:
    differences: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or "").lower()
        body = str(section.get("body") or "")
        body_lower = body.lower()
        bullets = [line for line in body.split("\n") if line.strip().startswith("- ")]
        harvest = (
            "compar" in title or "differ" in title
            or "comparison" in body_lower or "difference" in body_lower
        )
        if harvest:
            for bullet in bullets:
                cleaned = _strip_inline(bullet.strip()[2:])
                cleaned = _clean_difference(cleaned)
                if cleaned and cleaned not in differences:
                    differences.append(cleaned)
        for line in body.split("\n"):
            probe = line.strip().lstrip("*").strip()
            if probe.lower().startswith("key difference"):
                cleaned = _strip_inline(probe)
                cleaned = re.sub(
                    r"^key\s+differences?:?\s*", "", cleaned, flags=re.IGNORECASE
                )
                cleaned = _clean_difference(cleaned)
                if not cleaned or cleaned.startswith(("(", "[")):
                    continue
                if cleaned not in differences:
                    differences.append(cleaned)
    return differences


def _excerpt_text(excerpt: str) -> str:
    parts = [part.strip() for part in str(excerpt or "").split("|") if part.strip()]
    if len(parts) > 1:
        return parts[-1]
    return str(excerpt or "").strip()


def _sources(source_sections: list[dict]) -> list[dict]:
    sources = []
    for i, section in enumerate(source_sections, start=1):
        if not isinstance(section, dict):
            continue
        act = str(section.get("act") or "").strip()
        number = section.get("section") or section.get("section_number") or ""
        name = f"{act} Section {number}".strip()
        if name in ("", "Section"):
            name = str(section.get("title") or "").strip()
        excerpt = _strip_inline(_excerpt_text(section.get("excerpt") or ""))
        if len(excerpt) > 90:
            excerpt = excerpt[:89].rstrip() + "…"
        sources.append({
            "n": section.get("number") or i,
            "name": name,
            "note": excerpt,
        })
    return sources


def _timestamp(resp: dict) -> str:
    raw = resp.get("retrieved_at")
    if raw:
        try:
            if isinstance(raw, str):
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            elif isinstance(raw, datetime):
                parsed = raw
            else:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            pass
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def build_report_payload(resp: dict) -> dict:
    resp = resp or {}
    sections = [s for s in (resp.get("answer_sections") or []) if isinstance(s, dict)]
    full_answer = str(resp.get("generated_response") or "")

    tables = []
    for section in sections:
        tables.extend(_tables_in(section.get("body") or ""))

    statutory_rows = _statutory_rows(tables)
    if not statutory_rows:
        for i, section in enumerate(resp.get("source_sections") or [], start=1):
            if not isinstance(section, dict):
                continue
            act = str(section.get("act") or "").strip()
            number = section.get("section") or ""
            provision = f"{act} Section {number}".strip()
            if provision in ("", "Section"):
                provision = str(section.get("title") or "")
            text = _excerpt_text(section.get("excerpt") or "")
            statutory_rows.append({
                "provision": provision,
                "source": section.get("number") or i,
                "text": text,
            })

    comparison_rows = []
    for section in sections:
        rows = section.get("rows") or []
        if rows:
            comparison_rows = _comparison_rows_from_rows(rows)
            if comparison_rows:
                break
    if not comparison_rows:
        comparison_rows = _comparison_rows_from_tables(tables)

    confidence = resp.get("answer_confidence")
    try:
        confidence = float(confidence or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "query": str(resp.get("query") or ""),
        "route": str(resp.get("route") or ""),
        "confidence": confidence,
        "generated": _timestamp(resp),
        "direct_answer": _direct_answer(sections, full_answer),
        "statutory_rows": statutory_rows,
        "key_differences": _key_differences(sections),
        "comparison_rows": comparison_rows,
        "sources": _sources(resp.get("source_sections") or []),
    }
