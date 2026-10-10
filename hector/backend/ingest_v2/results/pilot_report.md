# HECTOR ingest_v2 pilot report - The Code of Criminal Procedure, 1973 (crpc-1973)

- source: sources/crpc-1973.pdf (261 pages as scanned)
- records written: 543 (output/crpc-1973.jsonl)
- gate summary: all gates OK
- seeds: G1 middle pages 20261010; A2 removed-line sample 20261012; step7 record sample 20261011
- external anchor: max plain section = 484 (expected 511) -> WARNING

## Gate table (G1-G9)

| Gate | Status | Evidence |
|---|---|---|
| G1 | **PASS** | page1 act_name=True, year=True; middle pages 76, 125, 131, 150, 155 all have markers (seed 20261010) |
| G2 | **PASS** | mode=toc; expected 532 sections; records 543; missing 0 []; extra 0 []; external anchor max_plain=484 vs 511 -> WARNING |
| G3 | **PASS** | part-0 records 532; prefix stripping needed 25; failures 0 |
| G4 | **PASS** | page-number lines 0; hyphen breaks 0; boilerplate 0; repeated>=30% pages 0 |
| G5 | **PASS** | records 543; duplicates []; empty []; non-nullable problems 0 |
| G6 | **PASS** | PRIMARY fragment windows 9675 total, 99.9587% found (>=99% required; reference get_text('text', sort=True)); DIAG whole-record 97.5962%, DIAG lines 99.9616%; failures 1 |
| G7 | **PASS** | parent order matches marker order; parts consistent; problems [] |
| G8 | **PASS** | limit 3000 chars; longest 170893; unflagged overs 0; flagged 20 |
| G9 | **PASS** | detected 272 = attached 207 + unattached 65; accounting_ok=True; records containing footnote lines 0 |

Notes:
- G2 is the ToC cross-check: every section listed in the book's Arrangement of Sections must have at least one record (100% coverage required; missing and extra numbers listed in gate evidence). Range markers count as covering their printed span; the external anchor 511 is reported separately above.
- G6 PRIMARY uses the A2 fragment-window definition; the whole-record window check and the cleaned-line check are DIAGNOSTIC (A2).

## Coverage / sequence detail (A4, A5, A6)

- accepted markers: 532; forms: {'M': 0, 'D': 532, 'R': 0}
- lettered/other non-plain numbers: 48 entries (25A, 41A, 41B, 41C, 41D, 50A, 53A, 54A, 55A, 60A, 105A, 105B...)
- rejected candidates: 247
- gaps: []
- A4 classification counts (number-lines): {'restated': 532, 'footnote': 240, 'UNKNOWN': 10}; unlabeled removals 0
- A4 UNKNOWN lines: 6 (full context in results/crpc-1973_numlines.json):
  - line 6788 p173: '409. Appeals to Court of Section how heard.—An appeal to the Court of Session or Sessions Judge shall'
  - line 14388 p259: '16. Insertion of new section 144A.—In Chapter X of the principal Act, under sub-heading'
  - line 14431 p260: '28. Amendment of section 320.—In section 320 of the principal Act, in the Table under sub-section'
  - line 14438 p260: '38. Amendment of section 438.—In section 438 of the principal Act, for sub-section (1), the'
  - line 14465 p261: '42. Amendment of the First Schedule.—In the First Schedule to the principal Act, under the'
  - line 14492 p261: '44. Amendment of Act 45 of 1860.—In the Indian Penal Code,—'
- A5 LOOKAHEAD_LINES=40, longest actually used=10, restated >2 pages away: []
- A6 scanner iterations: 3 of the A6 maximum (see ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.

## A1 page-joining evidence (first 5 page-spanning records)

- page-spanning records: 132
- section 2 pages p21-p23
  - join 21->22 removed between: ['footnote', 'page_number']
  - before: ...'r in writing to a Magistrate, with a view to his\ntaking action under this Code, that some person, whether known or unknown, has committed an'
  - after: 'offence, but does not include a police report.\nExplanation.—A report made by a police officer in a case which discloses, after investigation'
  - join 22->23 removed between: ['footnote', 'page_number']
  - before: ...'or specially by the State\nGovernment, to be a police station, and includes any local area specified by the State Government in\nthis behalf;'
  - after: '(t) “prescribed” means prescribed by rules made under this Code;\n(u) “Public Prosecutor” means any person appointed under section 24, and in'
  - join 23->23 removed between: ['header']
  - before: ...'used herein and not defined but defined in the Indian Penal Code\n(45 of 1860) have the meanings respectively assigned to them in that Code.'
  - after: 'Haryana\nIn section 2, for the words “State of Haryana”, the words “Union territory of Chandigarh” shall be\nsubstituted.\n[Vide Notification N'
- section 3 pages p23-p24
  - join 23->24 removed between: ['footnote', 'page_number']
  - before: ...'cement of this Code,—\n(a) to a Magistrate of the first class, shall be construed as a reference to a Judicial Magistrate of\nthe first class;'
  - after: '(b) to a Magistrate of the second class or of the third class, shall be construed as a reference to a\nJudicial Magistrate of the second clas'
  - join 24->24 removed between: ['header']
  - before: ...'e, sanctioning a prosecution or withdrawing from a prosecution,\nthey shall, subject as aforesaid, be exercisable by an Executive Magistrate.'
  - after: 'Andaman and Nicobar Islands (U.T.).\nInsertion of New section 3A. —In the Code, as it applies to the Union territory of Andaman and\nNicobar I'
- section 8 pages p25-p26
  - join 25->26 removed between: ['header', 'page_number']
  - before: ...'expression “population” means the population as\nascertained at the last preceding census of which the relevant figures have been published.'
  - after: 'Delhi\nIn its application to the National Capital Territory of Delhi, in section 8,—\n(a) in sub-section (1), for the words “a city or town”,'
- section 9 pages p26-p27
  - join 26->26 removed between: ['header']
  - before: ...'th the affairs of\nthe Union or of a State, where under any law, such appointment, posting or promotion is required to be\nmade by Government.'
  - after: 'West Bengal.—\nTo sub-section (3) of section 9 of the principal Act, the following provisos shall be added:—\nProvided that notwithstanding an'
  - join 26->27 removed between: ['page_number']
  - before: ...'d, wherein the headquarters of\nthe Sessions Judges are situated, exercising jurisdiction in a Court of Session, shall have all the powers of'
  - after: 'the Sessions Judge under this Code, in respect of the cases and proceedings in the Criminal Courts in that\nsub-division, for the purposes of'
- section 12 pages p27-p28
  - join 27->28 removed between: ['footnote', 'page_number']
  - before: ...'ied in this section as\noccasion requires.\n(b) Subject to the general control of the Chief Judicial Magistrate, every Sub-divisional Judicial'
  - after: 'Magistrate shall also have and exercise, such powers of supervision and control over the work of the\nJudicial Magistrates (other than Additi'

## A2 verbatim / removal labels

- A2 PRIMARY fragment windows: 99.9587% (threshold 99%)
- DIAGNOSTIC whole-record windows: 97.5962%
- DIAGNOSTIC cleaned-lines-in-raw: 99.9616%
- removal label counts: {'header': 221, 'footnote': 272, 'page_number': 864, 'separator': 66}; unlabeled removals: 0 (unlabeled = FAIL)
- 20-line removed sample printed with seed 20261012: see results/crpc-1973_step6_validate.log

## A3 statuses

- status counts: {'repealed': 543}
- R-form (omitted) sections: 

## 20 random records (seed 20261011)

### 1. crpc-1973:s:446:0
- number='446', title='Procedure when bond has been forfeited', chapter='CHAPTER XXXIII - PROVISIONS AS TO BAIL AND BONDS', pages 185-186, status=repealed, chars=2328, parts 1/1
- has: proviso=True, explanation=True, exception=False, illustration=False, amendment_notes=2
- text: 446. Procedure when bond has been forfeited.—(1) Where a bond under this Code is for appearance, or for production of property, before a Court and it is proved to the satisfaction of that Court, or of any Court to which the case has subsequ...

### 2. crpc-1973:s:307:0
- number='307', title='Power to direct tender of pardon', chapter='CHAPTER XXIV - GENERAL PROVISIONS AS TO INQUIRIES AND TRIALS', pages 134-134, status=repealed, chars=364, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 307. Power to direct tender of pardon.—At any time after commitment of a case but before judgment is passed, the Court to which the commitment is made may, with a view to obtaining at the trial the evidence of any person supposed to have be...

### 3. crpc-1973:s:449:0
- number='449', title='Appeal from orders under section 446', chapter='CHAPTER XXXIII - PROVISIONS AS TO BAIL AND BONDS', pages 186-186, status=repealed, chars=301, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 449. Appeal from orders under section 446.—All orders passed under section 446 shall be appealable,— (i) in the case of an order made by a Magistrate, to the Sessions Judge; (ii) in the case of an order made by a Court of Session, to the Co...

### 4. crpc-1973:s:300:0
- number='300', title='Person once convicted or acquitted not to be tried for same offence', chapter='CHAPTER XXIV - GENERAL PROVISIONS AS TO INQUIRIES AND TRIALS', pages 131-131, status=repealed, chars=554, parts 1/2
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 300. Person once convicted or acquitted not to be tried for same offence.—(1) A person who has once been tried by a Court of competent jurisdiction for an offence and convicted or acquitted of such offence shall, while such conviction or ac...

### 5. crpc-1973:s:251:0
- number='251', title='Substance of accusation to be stated', chapter='CHAPTER XX - TRIAL OF SUMMONS-CASES BY MAGISTRATES', pages 118-118, status=repealed, chars=605, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 251. Substance of accusation to be stated.—When in a summons-case the accused appears or is brought before the Magistrate, the particulars of the offence of which he is accused shall be stated to him, and he shall be asked whether he pleads...

### 6. crpc-1973:s:50:0
- number='50', title='Person arrested to be informed of grounds of arrest and of right to bail', chapter='CHAPTER V - ARREST OF  PERSONS', pages 42-42, status=repealed, chars=529, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 50. Person arrested to be informed of grounds of arrest and of right to bail.—(1) Every police officer or other person arresting any person without warrant shall forthwith communicate to him full particulars of the offence for which he is a...

### 7. crpc-1973:s:38:0
- number='38', title='Aid to person, other than police officer, executing warrant', chapter='CHAPTER IV - A.—POWERS OF SUPERIOR OFFICERS OF POLICE', pages 37-37, status=repealed, chars=297, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 38. Aid to person, other than police officer, executing warrant.—When a warrant is directed to a person other than a police officer, any other person may aid in the execution of such warrant, if the person to whom the warrant is directed be...

### 8. crpc-1973:s:318:0
- number='318', title='Procedure where accused does not understand proceedings', chapter='CHAPTER XXIV - GENERAL PROVISIONS AS TO INQUIRIES AND TRIALS', pages 138-138, status=repealed, chars=465, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 318. Procedure where accused does not understand proceedings.—If the accused, though not of unsound mind, cannot be made to understand the proceedings, the Court may proceed with the inquiry or trial; and, in the case of a Court other than ...

### 9. crpc-1973:s:437:0
- number='437', title='When bail may be taken in case of non-bailable offence', chapter='CHAPTER XXXIII - PROVISIONS AS TO BAIL AND BONDS', pages 179-181, status=repealed, chars=4736, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=6
- text: 437. When bail may be taken in case of non-bailable offence.—5[(1) When any person accused of, or suspected of, the commission of any non-bailable offence is arrested or detained without warrant by an officer in charge of a police station o...

### 10. crpc-1973:s:36:0
- number='36', title='Powers of superior officers of police', chapter='CHAPTER IV - A.—POWERS OF SUPERIOR OFFICERS OF POLICE', pages 36-36, status=repealed, chars=274, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 36. Powers of superior officers of police.—Police officers superior in rank to an officer in charge of a police station may exercise the same powers, throughout the local area to which they are appointed, as may be exercised by such officer...

### 11. crpc-1973:s:13:0
- number='13', title='Special Judicial Magistrates', chapter='CHAPTER II - CONSTITUTION OF CRIMINAL COURTS AND OFFICES', pages 28-28, status=repealed, chars=1763, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=2
- text: 13. Special Judicial Magistrates.—(1) The High Court may, if requested by the Central or State Government so to do, confer upon any person who holds or has held any post under the Government, all or any of the powers conferred or conferrabl...

### 12. crpc-1973:s:306:0
- number='306', title='Tender of pardon to accomplice', chapter='CHAPTER XXIV - GENERAL PROVISIONS AS TO INQUIRIES AND TRIALS', pages 133-134, status=repealed, chars=2287, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 306. Tender of pardon to accomplice.—(1) With a view to obtaining the evidence of any person supposed to have been directly or indirectly concerned in or privy to an offence to which this section applies, the Chief Judicial Magistrate or a ...

### 13. crpc-1973:s:193:0
- number='193', title='Cognizance of offences by Courts of Session', chapter='CHAPTER XIV - CONDITIONS REQUISITE FOR INITIATION OF PROCEEDINGS', pages 96-96, status=repealed, chars=317, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 193. Cognizance of offences by Courts of Session.—Except as otherwise expressly provided by this Code or by any other law for the time being in force, no Court of Session shall take cognizance of any offence as a Court of original jurisdict...

### 14. crpc-1973:s:109:0
- number='109', title='Security for good behaviour from suspected persons', chapter='CHAPTER VIII - SECURITY FOR KEEPING THE PEACE AND FOR GOOD BEHAVIOUR', pages 60-60, status=repealed, chars=568, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 109. Security for good behaviour from suspected persons.—When 1[an Executive Magistrate]  receives information that there is within his local jurisdiction a person taking precautions to conceal his presence and that there is reason to belie...

### 15. crpc-1973:s:431:0
- number='431', title='Money ordered to be paid recoverable as a fine', chapter='CHAPTER XXXII - EXECUTION, SUSPENSION, REMISSION AND COMMUTATION OF SENTENCES', pages 177-177, status=repealed, chars=631, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 431. Money ordered to be paid recoverable as a fine.—Any money (other than a fine) payable by virtue of any order made under this Code, and the method of recovery of which is not otherwise expressly provided for, shall be recoverable as if ...

### 16. crpc-1973:s:25:0
- number='25', title='Assistant Public prosecutors', chapter='CHAPTER II - CONSTITUTION OF CRIMINAL COURTS AND OFFICES', pages 32-33, status=repealed, chars=934, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 25. Assistant Public prosecutors.—(1) The State Government shall appoint in every district one or more Assistant  Public Prosecutors for conducting prosecutions in the Courts of Magistrates. 1[(1A) The Central Government may appoint one or ...

### 17. crpc-1973:s:3:1
- number='3', title='Construction of references', chapter='CHAPTER I - PRELIMINARY', pages 24-24, status=repealed, chars=2395, parts 2/2
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: (4) Where, under any law, other than this Code, the function exercisable by a Magistrate relate to matters,— (a) which involve the appreciation or sifting of evidence or the formulation of any decision which exposes any person to any punish...

### 18. crpc-1973:s:202:0
- number='202', title='Postponement of issue of process', chapter='CHAPTER XV - COMPLAINTS TO MAGISTRATES', pages 102-103, status=repealed, chars=1552, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 202. Postponement of issue of process.—(1) Any Magistrate, on receipt of a complaint of an offence of which he is authorised to take cognizance or which has been made over to him under section 192, may, if he thinks fit, 1[and shall, in a c...

### 19. crpc-1973:s:214:0
- number='214', title='Words in charge taken in sense of law under which offence is punishable', chapter='CHAPTER XVII - THE CHARGE', pages 107-107, status=repealed, chars=257, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 214. Words in charge taken in sense of law under which offence is punishable.—In every charge words used in describing an offence shall be deemed to have been used in the sense attached to them respectively by the law under which such offen...

### 20. crpc-1973:s:129:0
- number='129', title='Dispersal of assembly by use of civil force', chapter='CHAPTER X - MAINTENANCE OF PUBLIC ORDER AND TRANQUILLITY', pages 69-69, status=repealed, chars=1088, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 129. Dispersal of assembly by use of civil force.—(1) Any Executive Magistrate or officer in charge of a police station or, in the absence of such officer in charge, any police officer, not below the rank of a sub-inspector, may command any...

## Consumer Protection 2019 (paused at checkpoint 1)

- registry entry and source PDF present; inspection NOT run per instruction.
- when resumed, G2 must run in ToC mode: every expected section from the ToC needs >=1 record (100% required; missing/extra listed).

## Block-order note

- pages where raw extraction order differs from (y,x) reading order: 261/261 (total counter: {'pages': 889, 'diff_pages': 889}); (y,x) order kept. G6 evidence: see ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw reference).

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

- output/crpc-1973.jsonl (543 records)
- results/crpc-1973_gates.json, _clean.json, _segments.json, _flags.json, _assembly.json, _markers.json, _numlines.json, _expected.json, _expected_meta.json, _toc_meta.json
- results/crpc-1973_step2_inspect.log ... _crpc-1973_step7_report.log (one per step)
- results/pilot_report.md (this file)
