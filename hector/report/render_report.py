"""Fill the HECTOR report template with payload data (spec sections 9-10)."""

import os
import re
import sys
import time

from docxtpl import DocxTemplate

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
if REPORT_DIR not in sys.path:
    sys.path.insert(0, REPORT_DIR)

TEMPLATE_PATH = os.path.join(REPORT_DIR, "templates", "hector_report_template.docx")

NBSP = "\u00A0"
DASH = "—"
LDQUO = "\u201c"
RDQUO = "\u201d"

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_MD_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
_DASH_LINE_RE = re.compile(r"^\s*-{3,}\s*$")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s*")
_WS_RE = re.compile(r"\s+")


def _strip_markdown(text):
    lines = []
    for line in text.split("\n"):
        if _MD_LINE_RE.match(line) or _DASH_LINE_RE.match(line):
            continue
        lines.append(_HEADING_RE.sub("", line.strip()))
    out = "\n".join(lines)
    for token in ("**", "__", "`"):
        out = out.replace(token, "")
    return out


def _curly(text):
    out = []
    open_d = True
    for ch in text:
        if ch == '"':
            out.append(LDQUO if open_d else RDQUO)
            open_d = not open_d
        else:
            out.append(ch)
    text = "".join(out)
    text = re.sub(r"(?<=[A-Za-z0-9])'(?=[A-Za-z0-9])", "\u2019", text)
    out = []
    open_s = True
    for ch in text:
        if ch == "'":
            out.append("\u2018" if open_s else "\u2019")
            open_s = not open_s
        else:
            out.append(ch)
    return "".join(out)


def clean_line(value):
    if value is None:
        return ""
    text = _CONTROL_RE.sub("", str(value))
    text = _strip_markdown(text)
    text = _curly(text)
    return _WS_RE.sub(" ", text).strip()


def clean_paras(value):
    if value is None:
        return [""]
    text = _CONTROL_RE.sub("", str(value))
    text = _strip_markdown(text)
    text = _curly(text)
    paras = [_WS_RE.sub(" ", line).strip() for line in text.split("\n")]
    paras = [p for p in paras if p]
    return paras or [""]


def _tag(source_no):
    if source_no in (None, ""):
        return ""
    return "%s[Source%s%s]" % (NBSP, NBSP, source_no)


def _apply_rule5(raw_rows, key, src_key):
    texts = ["\n".join(r[key]) for r in raw_rows]
    cells = []
    for i, r in enumerate(raw_rows):
        text = texts[i].strip()
        dup = False
        if text:
            for j in range(i):
                if raw_rows[j]["point"] == r["point"]:
                    continue
                if texts[j].strip() == text:
                    dup = True
                    break
        if not text or dup:
            cells.append([{"text": DASH, "tag": ""}])
            continue
        paras = [{"text": p, "tag": ""} for p in r[key]]
        paras[-1]["tag"] = _tag(r[src_key])
        cells.append(paras)
    return cells


def prepare_context(data):
    ctx = {}
    ctx["query"] = clean_line(data.get("query"))
    ctx["route"] = clean_line(data.get("route"))
    ctx["confidence_text"] = "%.1f%%" % float(data.get("confidence") or 0.0)
    ctx["generated"] = clean_line(data.get("generated"))
    ctx["direct_answer"] = clean_line(data.get("direct_answer"))

    rows = []
    for r in data.get("statutory_rows") or []:
        paras = clean_paras(r.get("text"))
        if paras[0]:
            paras[0] = LDQUO + paras[0]
            paras[-1] = paras[-1] + RDQUO
        source_no = r.get("source")
        rows.append({
            "provision_paras": [{"text": clean_line(r.get("provision")),
                                 "tag": ""}],
            "source_paras": [{"text": "Source %s" % source_no
                              if source_no not in (None, "") else "",
                              "tag": ""}],
            "text_paras": [{"text": p, "tag": ""} for p in paras],
        })
    if not rows:
        rows.append({
            "provision_paras": [{"text": "None retrieved", "tag": ""}],
            "source_paras": [{"text": "", "tag": ""}],
            "text_paras": [{"text": "", "tag": ""}],
        })
    ctx["statutory_rows"] = rows

    diffs = [clean_line(d) for d in data.get("key_differences") or []]
    diffs = [d for d in diffs if d]
    ctx["key_differences"] = diffs or ["None retrieved"]

    raw = []
    for r in data.get("comparison_rows") or []:
        raw.append({
            "point": clean_paras(r.get("point")),
            "ipc": clean_paras(r.get("ipc")),
            "bns": clean_paras(r.get("bns")),
            "ipc_source": r.get("ipc_source"),
            "bns_source": r.get("bns_source"),
        })
    if raw:
        ipc_cells = _apply_rule5(raw, "ipc", "ipc_source")
        bns_cells = _apply_rule5(raw, "bns", "bns_source")
        ctx["comparison_rows"] = [
            {
                "point_paras": [{"text": p, "tag": ""}
                                for p in raw[i]["point"]],
                "ipc_paras": ipc_cells[i],
                "bns_paras": bns_cells[i],
            }
            for i in range(len(raw))
        ]
    else:
        ctx["comparison_rows"] = [{
            "point_paras": [{"text": "None retrieved", "tag": ""}],
            "ipc_paras": [{"text": "", "tag": ""}],
            "bns_paras": [{"text": "", "tag": ""}],
        }]

    sources = []
    for s in sorted(data.get("sources") or [], key=lambda s: s.get("n") or 0):
        try:
            number = "%02d" % int(s.get("n"))
        except (TypeError, ValueError):
            number = clean_line(s.get("n"))
        name = clean_line(s.get("name"))
        note = clean_line(s.get("note"))
        sources.append({
            "number": number,
            "name": name,
            "sep": " \u2014 " if note else "",
            "note_text": note,
        })
    if not sources:
        sources.append({"number": "01", "name": "None retrieved",
                        "sep": "", "note_text": ""})
    ctx["sources"] = sources
    return ctx


def render_report(data: dict, out_path: str) -> str:
    context = prepare_context(data)
    if not os.path.exists(TEMPLATE_PATH):
        import build_template
        build_template.build()
    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(context, autoescape=True)
    if out_path.lower().endswith(".docx"):
        final = out_path
        parent = os.path.dirname(final)
        if parent:
            os.makedirs(parent, exist_ok=True)
    else:
        os.makedirs(out_path, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        final = os.path.join(out_path, "HECTOR_Report_%s.docx" % stamp)
    tpl.save(final)
    print("created:", final)
    return final


if __name__ == "__main__":
    import json
    sample = os.path.join(REPORT_DIR, "sample_data.json")
    with open(sample, encoding="utf-8") as fh:
        payload = json.load(fh)
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPORT_DIR, "output")
    render_report(payload, dest)
