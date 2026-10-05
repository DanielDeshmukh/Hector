# HECTOR ingest_v2 pilot report - The Indian Penal Code, 1860 (ipc-1860)

- source: sources/ipc-1860.pdf (227 pages as scanned)
- records written: 552 (output/ipc-1860.jsonl)
- gate summary: all gates OK
- seeds: G1 middle pages 20261010; A2 removed-line sample 20261012; step7 record sample 20261011
- external anchor: max plain section = 511 (expected 511) -> OK

## Gate table (G1-G9)

| Gate | Status | Evidence |
|---|---|---|
| G1 | **PASS** | page1 act_name=True, year=True; middle pages 62, 86, 101, 141, 159 all have markers (seed 20261010) |
| G2 | **SEQUENCE_ONLY** | mode=sequence_only; 551 markers strictly increasing=True; covered [1, 511]; gaps=[] (total 0); external anchor max_plain=511 vs 511 -> OK |
| G3 | **PASS** | part-0 records 551; prefix stripping needed 1; failures 0 |
| G4 | **PASS** | page-number lines 0; hyphen breaks 0; boilerplate 0; repeated>=30% pages 0 |
| G5 | **PASS** | records 552; duplicates []; empty []; non-nullable problems 0 |
| G6 | **PASS** | PRIMARY fragment windows 6310 total, 100.0% found (>=99% required; reference get_text('text', sort=True)); DIAG whole-record 99.1011%, DIAG lines 100.0%; failures 0 |
| G7 | **PASS** | parent order matches marker order; parts consistent; problems [] |
| G8 | **PASS** | limit 3000 chars; longest 8655; unflagged overs 0; flagged 9 |
| G9 | **PASS** | detected 690 = attached 656 + unattached 34; accounting_ok=True; records containing footnote lines 0 |

Notes:
- G2 is reported as SEQUENCE_ONLY and never PASS: the IPC PDF has no table of contents, so coverage is proven by a strictly increasing, gapless accepted sequence (1..511) plus the external anchor 511, not by a ToC cross-check. The ToC cross-check mode is reserved for Consumer Protection 2019.
- G6 PRIMARY uses the A2 fragment-window definition; the whole-record window check and the cleaned-line check are DIAGNOSTIC (A2).

## Coverage / sequence detail (A4, A5, A6)

- accepted markers: 551; forms: {'M': 535, 'D': 1, 'R': 15}
- lettered/other non-plain numbers: 45 entries (52A, 53A, 55A, 108A, 120A, 120B, 121A, 124A, 138A, 153A, 153B, 161 to 165A...)
- rejected candidates: 279
- gaps: []
- A4 classification counts (number-lines): {'margin': 550, 'restated': 547, 'footnote': 284, 'UNKNOWN': 2}; unlabeled removals 0
- A4 UNKNOWN lines: 2 (full context in results/ipc-1860_numlines.json):
  - line 2068 p53: '121.--Whoever within or without 2*[India] conspires to commit any'
  - line 3689 p91: '460.]'
- A5 LOOKAHEAD_LINES=40, longest actually used=17, restated >2 pages away: []
- A6 scanner iterations: 3 of the A6 maximum (see ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.

## A1 page-joining evidence (first 5 page-spanning records)

- page-spanning records: 171
- section 3 pages p1-p2
- section 4 pages p2-p3
  - join 2->3 removed between: ['footnote', 'page_number', 'separator']
  - before: ...'any citizen\nof India\nin any place without and\nbeyond India;\n(2) any person on any ship or aircraft registered in India\nwherever it may be.]'
  - after: 'Explanation.\nExplanation.--In this section the word "offence" includes every\nact committed outside 1*[India] which, if committed in 1*[India'
- section 6 pages p3-p4
- section 10 pages p4-p5
- section 19 pages p6-p7

## A2 verbatim / removal labels

- A2 PRIMARY fragment windows: 100.0% (threshold 99%)
- DIAGNOSTIC whole-record windows: 99.1011%
- DIAGNOSTIC cleaned-lines-in-raw: 100.0%
- removal label counts: {'separator': 128, 'footnote': 690, 'page_number': 119, 'header': 101}; unlabeled removals: 0 (unlabeled = FAIL)
- 20-line removed sample printed with seed 20261012: see results/ipc-1860_step6_validate.log

## A3 statuses

- status counts: {'repealed': 537, 'omitted': 15}
- R-form (omitted) sections: 13, 138A, 15, 16, 161 to 165A, 226, 478, 480, 490, 492, 56, 58, 59, 61, 62

## 20 random records (seed 20261011)

### 1. ipc-1860:s:470:0
- number='470', title='Forged document', chapter='CHAPTER XVIII', pages 205-205, status=repealed, chars=130, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 470. Forged document. 470. Forged document.--A false document made wholly or in part by forgery is designated "a forged document"....

### 2. ipc-1860:s:329:0
- number='329', title='Voluntarily causing grievous hurt to extort property, or to constrain to an illegal act', chapter='CHAPTER XVI - OF OFFENCES AFFECTING THE HUMAN BODY', pages 146-146, status=repealed, chars=680, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 329. Voluntarily causing grievous hurt to extort property, or to constrain to an illegal act. 329. Voluntarily causing grievous hurt to extort property, or to constrain to an illegal act.--Whoever voluntarily causes grievous hurt for the pu...

### 3. ipc-1860:s:474:0
- number='474', title='Having possession of document described in section 466 or 467, knowing it to be forged and intending to use it genuine', chapter='CHAPTER XVIII', pages 206-207, status=repealed, chars=869, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 474. Having possession of document described in section 466 or 467, knowing it to be forged and intending to use it genuine. 474. Having possession of document described in section 466 or 467, knowing it to be forged and intending to use it...

### 4. ipc-1860:s:321:0
- number='321', title='Voluntarily causing hurt', chapter='CHAPTER XVI - OF OFFENCES AFFECTING THE HUMAN BODY', pages 143-143, status=repealed, chars=298, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 321. Voluntarily causing hurt. 321. Voluntarily causing hurt.--Whoever does any act with the intention of thereby causing hurt to any person, or with the knowledge that he is likely thereby to cause hurt to any person, and does thereby caus...

### 5. ipc-1860:s:264:0
- number='264', title='Fraudulent use of false instrument for weighing', chapter='CHAPTER XIII - OF OFFENCES RELATING TO WEIGHTS AND MEASURES', pages 119-119, status=repealed, chars=318, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 264. Fraudulent use of false instrument for weighing. 264. Fraudulent use of false instrument for weighing.--Whoever, fraudulently uses any instrument for weighing which he knows to be false, shall be punished with imprisonment of either de...

### 6. ipc-1860:s:54:0
- number='54', title='Commutation of sentence of death', chapter='CHAPTER III - OF PUNISHMENTS', pages 20-21, status=repealed, chars=285, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 54. Commutation of sentence of death. 54. Commutation of sentence of death.--In every case in which sentence of death shall have been passed, 3*[the appropriate Government] may, without the consent of the offender, commute the punishment fo...

### 7. ipc-1860:s:40:0
- number='40', title='"Offence"', chapter='CHAPTER II - GENERAL EXPLANATIONS', pages 16-16, status=repealed, chars=829, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=5
- text: 40. "Offence". 1*[40. "Offence".--Except in the 2*[Chapters] and sections mentioned in clauses 2 and 3 of this section, the word "offence" denotes a thing made punishable by this Code. In Chapter IV, 3*[Chapter VA] and in the following sect...

### 8. ipc-1860:s:341:0
- number='341', title='Punishment for wrongful restraint', chapter='CHAPTER XVI - OF OFFENCES AFFECTING THE HUMAN BODY', pages 150-150, status=repealed, chars=273, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 341. Punishment for wrongful restraint. 341. Punishment for wrongful restraint.--Whoever wrongfully restrains any person shall be punished with simple imprisonment for a term which may extend to one month, or with fine which may extend to f...

### 9. ipc-1860:s:458:0
- number='458', title='Lurking house-trespass or house-breaking by night after preparation for hurt, assault, or wrongful restraint', chapter='CHAPTER XVII - OF OFFENCES AGAINST PROPERTY', pages 199-200, status=repealed, chars=657, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 458. Lurking house-trespass or house-breaking by night after preparation for hurt, assault, or wrongful restraint. 458. Lurking house-trespass or house-breaking by night after preparation for hurt, assault, or wrongful restraint.--Whoever c...

### 10. ipc-1860:s:38:0
- number='38', title='Persons concerned in criminal Act may be guilty of different offences', chapter='CHAPTER II - GENERAL EXPLANATIONS', pages 15-15, status=repealed, chars=701, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=True, amendment_notes=0
- text: 38. Persons concerned in criminal Act may be guilty of different offences. 38. Persons concerned in criminal Act may be guilty of different offences.--Where several persons are engaged or concerned in the commission of a criminal act, they ...

### 11. ipc-1860:s:15:0
- number='15', title='Definition of "British India"', chapter='CHAPTER II - GENERAL EXPLANATIONS', pages 6-6, status=omitted, chars=60, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 15. [Definition of "British India".] Rep. by the A. O. 1937....

### 12. ipc-1860:s:328:0
- number='328', title='Causing hurt by means of poison, etc., with intent to commit and offence', chapter='CHAPTER XVI - OF OFFENCES AFFECTING THE HUMAN BODY', pages 145-146, status=repealed, chars=603, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 328. Causing hurt by means of poison, etc., with intent to commit and offence. 328. Causing hurt by means of poison, etc., with intent to commit and offence.--Whoever administers to or causes to be taken by any person any poison or any stup...

### 13. ipc-1860:s:207:0
- number='207', title='Fraudulent claim to property to prevent its seizure as forfeited or in execution', chapter='CHAPTER XI - OF FALSE EVIDENCE AND OFFENCES AGAINST PUBLIC JUSTICE', pages 92-93, status=repealed, chars=979, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 207. Fraudulent claim to property to prevent its seizure as forfeited or in execution. 207. Fraudulent claim to property to prevent its seizure as forfeited or in execution.--Whoever fraudulently accepts, receives or claims any property or ...

### 14. ipc-1860:s:503:0
- number='503', title='Criminal intimidation', chapter='CHAPTER XXII - OF CRIMINAL INTIMIDATION, INSULT AND ANNOYANCE', pages 222-223, status=repealed, chars=781, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=True, amendment_notes=0
- text: 503. Criminal intimidation. 503. Criminal intimidation.--Whoever threatens another with any injury to his person, reputation or property, or to the person or reputation of any one in whom that person is interested, with intent to cause alar...

### 15. ipc-1860:s:124:0
- number='124', title='Assaulting President, Governor, etc., with intent to compel or restrain the exercise of any lawful power', chapter='CHAPTER VI - OF OFFENCES AGAINST THE STATE', pages 54-55, status=repealed, chars=832, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=7
- text: 124. Assaulting President, Governor, etc., with intent to compel or restrain the exercise of any lawful power. 124. Assaulting President, Governor, etc., with intent to compel or restrain the exercise of any lawful power.--Whoever, with the...

### 16. ipc-1860:s:450:0
- number='450', title='House-trespass in order to commit offence punishable with imprisonment for life', chapter='CHAPTER XVII - OF OFFENCES AGAINST PROPERTY', pages 197-197, status=repealed, chars=416, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 450. House-trespass in order to commit offence punishable with imprisonment for life. 450. House-trespass in order to commit offence punishable with imprisonment for life.--Whoever commits house-trespass in order to the committing of any of...

### 17. ipc-1860:s:26:0
- number='26', title='"Reason to believe"', chapter='CHAPTER II - GENERAL EXPLANATIONS', pages 11-11, status=repealed, chars=172, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 26. "Reason to believe". 26. "Reason to believe".--A person is said to have "reason to believe" a thing, if he has sufficient cause to believe that thing but not otherwise....

### 18. ipc-1860:s:4:0
- number='4', title='Extension of Code to extra-territorial offences', chapter='CHAPTER I - INTRODUCTION', pages 2-3, status=repealed, chars=691, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=8
- text: 4. Extension of Code to extra-territorial offences. 8*[4. Extension of Code to extra-territorial offences.--The provisions of this Code apply also to any offence committed by- 9*[(1) any citizen of India in any place without and beyond Indi...

### 19. ipc-1860:s:218:0
- number='218', title='Public servant framing incorrect record or writing with intent to save person from punishment or property from forfeiture', chapter='CHAPTER XI - OF FALSE EVIDENCE AND OFFENCES AGAINST PUBLIC JUSTICE', pages 100-100, status=repealed, chars=977, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 218. Public servant framing incorrect record or writing with intent to save person from punishment or property from forfeiture. 218. Public servant framing incorrect record or writing with intent to save person from punishment or property f...

### 20. ipc-1860:s:228:0
- number='228', title='Intentional insult or interruption to public servant sitting in judicial proceeding', chapter='CHAPTER XI - OF FALSE EVIDENCE AND OFFENCES AGAINST PUBLIC JUSTICE', pages 105-105, status=repealed, chars=501, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 228. Intentional insult or interruption to public servant sitting in judicial proceeding. 228. Intentional insult or interruption to public servant sitting in judicial proceeding.--Whoever intentionally offers any insult, or causes any inte...

## Consumer Protection 2019 (paused at checkpoint 1)

- registry entry and source PDF present; inspection NOT run per instruction.
- when resumed, G2 must run in ToC mode: every expected section from the ToC needs >=1 record (100% required; missing/extra listed).

## Block-order note

- pages where raw extraction order differs from (y,x) reading order: 122/227 (total counter: {'pages': 227, 'diff_pages': 122}); (y,x) order kept. G6 evidence: see ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw reference).

## ASSUMPTIONS (verbatim from SPEC.md)

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


## Files produced

- output/ipc-1860.jsonl (552 records)
- results/ipc-1860_gates.json, _clean.json, _segments.json, _flags.json, _assembly.json, _markers.json, _numlines.json, _expected.json, _expected_meta.json, _toc_meta.json
- results/ipc-1860_step2_inspect.log ... _ipc-1860_step7_report.log (one per step)
- results/pilot_report.md (this file)
