#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_lines.py - print line/label/cls around a given line index."""

import sys

import v2_common as V
import v2_scanner as S

ACT = "ipc-1860"
LO = int(sys.argv[1]) if len(sys.argv) > 1 else 17
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 36
V.tee(f"{ACT}_diag_lines_{LO}_{HI}")

reg = V.load_registry()
act = [a for a in reg if a["act_id"] == ACT][0]
doc = V.fitz.open(str(V.SOURCES / act["source_file"].split("/")[-1]))
sc = S.scan_document(doc)
lines = sc["lines"]
for k in range(LO, min(HI, len(lines))):
    ln = lines[k]
    print(k, "p" + str(ln["page"] + 1), "lbl=" + str(ln["label"]),
          "cls=" + str(ln["cls"]), repr(ln["text"][:75]), flush=True)
doc.close()
