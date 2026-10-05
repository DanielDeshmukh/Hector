#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One-shot: append ASSUMPTIONS to SPEC.md and the STEP 2 line to PROGRESS.md."""

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="backslashreplace")
D = os.path.dirname(os.path.abspath(__file__))

ASSUMPTIONS = """

ASSUMPTIONS (stricter interpretations, recorded as directed):
- Blank lines are dropped during scan extraction; continuity across every removal
  is proven instead by the A2 fragment-window check against raw normalized pages.
- Hyphen line-breaks are merged keeping the hyphen ("word-" + "line" -> "word-line").
- A printed range line (e.g. "161 to 165A.Rep. by ...") is ONE marker with its
  printed number; covers = plain bases 161..165, used only for the G2 gap set.
- A restated line whose printed number differs from the margin number but is at
  most MISTYPE_TOLERANCE=100 below it is taken as that section restated (source
  misprint, e.g. "320." printed where "330." belongs). General constant, no
  per-section rules.
- A bare repeated margin number ("334." again inside its window) is taken as the
  restated start (word-per-line heading layout).
- Footnote-reference prefixes are stripped with or without a bracket
  ("1*[14." and "1*479.").
- Any number already accepted is rejected if offered again as margin/direct
  candidate (wrapped title fragments like a lone "216A." must not re-accept).
- A bracketed Rep./omitted inside a section own heading region (never crossing
  into the next marker) downgrades form to R and status to omitted.
- Scanner iterations used: 3 of the A6 maximum. run1 = 9 gaps; run2 = year-line
  and misprint regressions found and fixed; run3 = 0 gaps in 1..511, anchor 511 OK.
"""

PROGRESS_LINE = (
    "- STEP 2 done (SEQUENCE_ONLY, external run 3 of A6 budget): 551 markers "
    "(M=534, D=1, R=16), 0 gaps in 1..511, anchor max_plain=511 OK, UNKNOWN=2, "
    "unlabeled removals=0; scanner in v2_scanner.py, reporting in "
    "step2_inspect.py; outputs results/ipc-1860_{step2_inspect.log,markers.json,"
    "expected.json,expected_meta.json,numlines.json,toc_meta.json}\n"
)

spec = os.path.join(D, "SPEC.md")
t = open(spec, encoding="utf-8").read()
if "ASSUMPTIONS" not in t:
    open(spec, "w", encoding="utf-8").write(t + ASSUMPTIONS)
    print("SPEC ASSUMPTIONS appended")
else:
    print("ASSUMPTIONS already present")

prog = os.path.join(D, "PROGRESS.md")
t2 = open(prog, encoding="utf-8").read()
if "STEP 2 done" not in t2:
    open(prog, "a", encoding="utf-8").write(PROGRESS_LINE)
    print("PROGRESS step2 appended")
else:
    print("PROGRESS step2 already present")
