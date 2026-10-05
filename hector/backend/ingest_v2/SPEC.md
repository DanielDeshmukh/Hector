RECORD SCHEMA: exactly these 27 keys, in this order, one JSON object per line.
 1 id: str, "<act_id>:s:<number lowercased>:<part_index>", e.g. "ipc-1860:s:302:0"
 2 act_id: str
 3 act_name: str (official title as printed on page 1)
 4 act_short: str
 5 unit_type: str, always "section" for now
 6 number: str as printed, e.g. "302", "120A"
 7 title: str or null (null only if the source has none)
 8 chapter: str or null
 9 hierarchy_path: str, "<act_short> > <chapter> > Section <number>"
10 text: str, verbatim cleaned section text INCLUDING provisos, explanations,
    exceptions, illustrations. Only whitespace and hyphen-break fixes. Keep inline
    amendment brackets such as 1*[...] exactly as in the PDF.
11 embedding_text: str, "<act_short> <year> | <chapter> | Section <number>: <title>\n<text>"
    (add " (part i/n)" to the header for split parts)
12 has_proviso: bool, text matches /\bProvided (further )?that\b/
13 has_explanation: bool, a line starts with "Explanation"
14 has_exception: bool, a line starts with "Exception"
15 has_illustration: bool, a line starts with "Illustration"
16 parent_id: str, "<act_id>:s:<number lowercased>"
17 part_index: int, 0-based
18 part_count: int
19 source_file: str
20 source_type: str, "bare_act"
21 page_start: int
22 page_end: int
23 status: str, "in_force" | "repealed" | "omitted"
24 repealed_on: str or null (ISO date)
25 replaced_by: str or null
26 amendment_notes: list[str]
27 content_hash: str, sha256 of text
Nullable keys: title, chapter, repealed_on, replaced_by. All others must be non-null.
"expected_source" is NOT a schema key; it appears in the report only.

GATES G1-G9 (print a PASS/FAIL table with evidence for each):
G1 identity: page 1 contains the registry act_name and year (case and whitespace
   insensitive); 5 random middle pages (seed 20261010) each contain at least one
   section marker from the accepted marker list. PASS only if all hold.
G2 coverage:
   - With a ToC (needed for Consumer Protection later): every expected section has
     at least one record; 100% required; list missing and extra numbers.
   - SEQUENCE_ONLY (IPC now): accepted markers must be strictly increasing; plain
     numbers must run 1..max with every gap listed with the text around it. Report the
     status as SEQUENCE_ONLY, never PASS. External cross-check: IPC max plain section
     is 511; a mismatch is a WARNING with evidence.
G3 every part-0 record's text starts with its own section number. Before checking,
   strip leading footnote-reference prefixes (like "1", "1*", "*", "[") and margin-heading
   duplicates; report how many records needed prefix stripping.
G4 clean text: zero standalone page-number lines (^\s*\d{1,3}\s*$); zero non-whitelisted
   lines repeated on >=30% of pages (whitelist: Illustration(s), Explanation,
   Exception(s), Provided, Chapter, Part, Schedule); zero "[a-z]-\n[a-z]" hyphen breaks;
   zero boilerplate lines ("This Bare Act is a government source...", separator
   lines made of dashes).
G5 integrity: ids unique; text non-empty after strip; every non-nullable key present
   and non-null; amendment_notes is a list.
G6 verbatim: PRIMARY = split each record's whitespace-normalized text into 60-character
   windows; >=99% of windows must appear in the whitespace-normalized RAW page text of
   pages page_start..page_end (after hyphen-break repair). DIAGNOSTIC (report only) =
   share of cleaned lines found as raw lines. Report the failure rate and 5 examples.
G7 order: records follow accepted-marker order; part_index values are contiguous from 0
   and part_count matches the number of parts.
G8 size: no record text over 3000 characters unless flagged LONG_UNSPLIT; list all
   flagged ones.
G9 footnote accounting: footnote lines detected = attached + unattached; no footnote
   line remains inside any record's text; report the unattached count.

AMENDMENTS (supersede conflicting text)
A1 PAGE-SPANNING SECTIONS: footnote zones and page separators are REMOVED, and the
   section text RESUMES on the following page. A record must never end at the first
   footnote or separator. Test: print 5 records where page_start != page_end,
   showing the text around each page join to prove continuity.
A2 G6 PRIMARY redefinition (decided before any results): the cleaner records the
   offsets of every removal (a "join point"). Split each record's text at its join
   points; take 60-character windows only WITHIN each fragment; >=99% of windows
   must appear in the whitespace-normalized RAW page text of pages
   page_start..page_end. ALSO REQUIRED: every removed line carries a rule label
   (page_number, separator, footnote, header, boilerplate); unlabeled removals = FAIL;
   print the counts per label and a random sample of 20 removed lines (seed
   20261012). The literal whole-record window check from the original spec is still
   computed and printed as a DIAGNOSTIC. Report all three numbers.
A3 STATUS: a section matched by the R form (Rep./omitted/bracketed removal) gets
   status "omitted". All other sections get the registry act-level status
   ("repealed" for IPC) with repealed_on and replaced_by from the registry.
A4 CLASSIFICATION LOG: every line starting with a number-and-dot is classified as
   margin, restated, footnote, or UNKNOWN. Save results/ipc-1860_numlines.json and
   report the counts per class, 20 sampled footnote classifications, and every UNKNOWN
   with context. Any gap in the accepted sequence is a FAIL for G2 (not a note).
A5 LOOKAHEAD: make the forward-window length a named constant, report its value
   and the longest lookahead actually used, and list any section whose restated
   marker was found more than 2 pages after its margin.
A6 NO HARDCODING of section numbers, titles or counts. Improve the scanner by
   general rules based on results/ipc-1860_diag_*.log only. If gaps remain, you may
   iterate at most 3 times, then report the remaining gaps with context.
A7 FOOTNOTE ATTACHMENT BY REFERENCE (page-scoped). Footnote numbers restart on each
   page, so matching must be page-scoped. For each page, list the inline reference
   markers found in that page's body text (forms like "N*[", "N[", superscript digit),
   with the section each belongs to (by position on the page). Match each footnote
   in that page's footer to a marker with the same number on the SAME page. Remove
   the positional "last marker at group start" rule entirely. A footnote with no
   same-page marker is UNATTACHED: report it, do not force it onto a section.
   Update G9: detected = attached_by_reference + unattached. Report counts, and 25
   random attachments (seed 20261014) showing footnote text, matched marker, record
   id and the 80 characters around the marker.
A8 SPLITTING: allowed cut points are only (a) between top-level sub-sections "(1)",
   "(2)" and (b) never inside an Illustration, Explanation, Exception or Proviso
   block, and never inside an open bracket. If no safe cut point exists below the
   size limit, do NOT split: keep the section whole and flag LONG_UNSPLIT, with its
   length. Re-run, then print the old and new part counts per section, the list of
   LONG_UNSPLIT records, and 150-character before/after context for every cut that
   remains. A hard cut at an exact character count is a FAIL.
A9 RANGE RECORDS: do not change the 27-key schema. Write output/ipc-1860_aliases.json
   mapping every section number covered by a range record to that record's id. Derive
   the covered numbers from the range text and the accepted sequence by a general
   rule; do not hardcode numbers. Print the mapping.
A10 SOURCE CURRENCY CHECK (read-only, report only):
   - PDF metadata (creation and modification dates) and any "as amended up to" text
     on the first pages.
   - From the footnote lines, extract every "Act N of YYYY" or "Act YYYY" reference
     and report the HIGHEST year found and the 10 most recent amending acts named.
   - External anchor supplied by the user, NOT an authority: sections 326A, 326B,
     354A, 354B, 354C, 354D, 370A, 376AB, 376DA, 376DB and 376E should exist if the
     source includes the 2013 and 2018 criminal law amendments. Report which are
     present and which are absent.
   - State plainly: if they are absent, this PDF predates those amendments and must
     be replaced with the official India Code copy.


A7b PRINTED-PAGE SCOPE BOUNDARIES (supersedes A7's "same page" wording: page means
    PRINTED page, not PDF page). Footnote numbering restarts on each printed page,
    and a printed page can start on the previous PDF page (evidence:
    results/visual/ipc_13_p5.png = folio 103, ipc_21_p7.png = folio 104; the folio
    line follows the previous page's footnote block, i.e. sits at the top of its own
    printed page). Before any label removal, record every standalone page-number line
    (kind == page_number) as a SCOPE BOUNDARY with its position in the stitched
    stream; removal itself is unchanged and G4 still applies. The matching span for a
    footnote block is (previous boundary, boundary following the footnote block].
    Within that span, match the footnote number to the same-number inline reference
    marker; if two markers carry the same number, attach to the NEAREST PRECEDING
    marker; if none precedes, the nearest FOLLOWING marker. No same-number marker in
    the span -> UNATTACHED: report it, do not force it onto a section. The positional
    "last marker at group start" rule stays removed. REPORT: scope boundaries found;
    attached by reference / unattached / ambiguous counts (ambiguous = footnote number
    not parseable, or its marker precedes the first section marker of the span); old
    vs new counts against the round-1 audit (19 by reference, 1 fallback, 60
    ambiguous); 25 random attachments (seed 20261014) each with footnote text,
    matched marker, record id and the 80 characters around the marker; and the
    footnote groups for PDF pages 5 (printed folio 103) and 7 (printed folio 104)
    with the sections each footnote matched.
A8b ORDINAL CLAUSES (addition to A8): in addition to top-level "(1)", "(2)", a cut
    is allowed immediately before a line starting with an ordinal clause marker
    ("First.--", "Second.--", ... double dash only). Still never cut inside an open
    bracket or inside an Illustration, Explanation, Exception or Proviso block.
    Patterns like "First.-That" (proviso) and "First Exception.-" are NOT cut points.
    If no safe cut point exists below the size limit, keep the section whole and flag
    LONG_UNSPLIT with its length.

A7c MULTI-OWNER ATTACHMENT (supersedes item 2 of A7b where they conflict).
    Evidence: results/visual/ipc_302_p136.png, ipc_304A_p137.png,
    ipc_498A_p217.png, ipc_21_p7.png.
    1. Within a scope span (between two printed-page-number boundaries), attach a
       footnote to EVERY section whose text has an inline marker with that number
       in that span, not just the nearest one. Example: footnote 1 on printed
       page 170 applies to 302, 303 and 304; footnote 2 to 304A; footnote 3 to
       304B. Store the text in each owning section's amendment_notes.
    2. A marker inside a chapter heading ("1*[CHAPTER XXA") is a chapter-level
       note: attach it to the first section of that chapter and report it as
       chapter_note.
    3. Footnote blocks and printed page numbers can fall in the MIDDLE of a
       section (498A: Explanation (a)/(b) comes after footnote 1 and page number
       212). Remove them and keep the section running. Printed page numbers are
       scope boundaries first, then removed.
    4. Recognise chapter headings with letter suffixes ("CHAPTER XXA") and
       restated headings with an opening bracket. A chapter heading must never
       be included in the previous section's text: record 498 must end at
       "or with both."
    5. Verify and print these cases (full record text plus amendment_notes):
       a. 498A: includes the Explanation (a) and (b); chapter = XXA with its
          title; the chapter note is attached
       b. 498: no "CHAPTER XXA" in its text
       c. 302, 303, 304: all carry footnote 1; 304A carries 2; 304B carries 3
       d. 300: continuous across the "167" page number, reading "...or-" then
          "2ndly"; "167" absent from the text
       e. 304: continuous across the PDF page break ("such bodily injury"
          followed by "as is likely to cause death;")
       f. 19(c) and 20's Illustration carry the footnote 5 "Rep. by the Madras
          Civil Courts Act"; 21's "5*[Third." does NOT
       g. 13: omitted, text verbatim
    6. Also report source typos found: list "Jutsice", "he likely" and ". or"
       occurrences, verbatim, and do NOT correct them.

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
- G6 raw reference = PyMuPDF get_text("text", sort=True) (raw page content in the
  page's own line reading order; no content modification by us). Evidence: the
  default (block-index) order places a ghost whitespace-only block ahead of the
  heading on page 2, dragging a separator rule that physically sits at y=324
  (above the footnote zone at y=329) into the join; default order failed exactly
  89 windows, one at each of the 87 page-joins (98.5895%), while sort=True found
  6310/6310 = 100% (logs: results/ipc-1860_diag_g6{,b}.log). Cleaned reading
  order was verified physically correct and was not changed to fit the raw.
