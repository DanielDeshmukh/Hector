#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Diagnostic: verify each R-form downgrade source line and its label."""

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="backslashreplace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import fitz  # noqa: E402

import v2_common as V  # noqa: E402
import v2_scanner as S  # noqa: E402

acts = V.load_registry()
act = next(a for a in acts if a["act_id"] == "ipc-1860")
src = V.SOURCES / act["source_file"].split("/")[-1]
doc = fitz.open(src)
scan = S.scan_document(doc)
lines = scan["lines"]
mk = scan["markers"]
print("markers:", len(mk))
for idx, m in enumerate(mk):
    if m["form"] != "R":
        continue
    anchor = m["restated"] if m["restated"] is not None else m["line"]
    nxt = mk[idx + 1]["line"] if idx + 1 < len(mk) else len(lines)
    hits = [(k, lines[k]["label"], lines[k]["cls"], lines[k]["text"][:78])
            for k in range(m["line"], min(anchor + 7, nxt))
            if S.REP_RE.search(lines[k]["text"])]
    print(f"{m['number']}: line={m['line']} anchor={anchor} hits={hits}")
doc.close()
print("[exit] 0")
