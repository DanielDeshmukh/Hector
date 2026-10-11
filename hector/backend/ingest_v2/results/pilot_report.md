# HECTOR ingest_v2 pilot report - The Limitation Act, 1963 (limitation-1963)

- source: sources/limitation-1963.pdf (24 pages as scanned)
- records written: 32 (output/limitation-1963.jsonl)
- gate summary: all gates OK
- seeds: G1 middle pages 20261010; A2 removed-line sample 20261012; step7 record sample 20261011
- external anchor: max plain section = 32 (expected 511) -> WARNING

## Gate table (G1-G9)

| Gate | Status | Evidence |
|---|---|---|
| G1 | **PASS** | page1 act_name=True, year=True; middle pages 7, 10, 11, 12, 18 all have markers (seed 20261010) |
| G2 | **PASS** | mode=toc; expected 32 sections; records 32; missing 0 []; extra 0 []; external anchor max_plain=32 vs 511 -> WARNING |
| G3 | **PASS** | part-0 records 32; prefix stripping needed 0; failures 0 |
| G4 | **PASS** | page-number lines 0; hyphen breaks 0; boilerplate 0; repeated>=30% pages 0 |
| G5 | **PASS** | records 32; duplicates []; empty []; non-nullable problems 0 |
| G6 | **PASS** | PRIMARY fragment windows 490 total, 99.7959% found (>=99% required; reference get_text('text', sort=True)); DIAG whole-record 97.992%, DIAG lines 100.0%; failures 1 |
| G7 | **PASS** | parent order matches marker order; parts consistent; problems [] |
| G8 | **PASS** | limit 3000 chars; longest 3533; unflagged overs 0; flagged 1 |
| G9 | **PASS** | detected 939 = attached 5 + unattached 934; accounting_ok=True; records containing footnote lines 0 |

Notes:
- G2 is the ToC cross-check: every section listed in the book's Arrangement of Sections must have at least one record (100% coverage required; missing and extra numbers listed in gate evidence). Range markers count as covering their printed span; the external anchor 511 is reported separately above.
- G6 PRIMARY uses the A2 fragment-window definition; the whole-record window check and the cleaned-line check are DIAGNOSTIC (A2).

## Coverage / sequence detail (A4, A5, A6)

- accepted markers: 32; forms: {'M': 0, 'D': 30, 'R': 2}
- lettered/other non-plain numbers: 0 entries ()
- rejected candidates: 150
- gaps: []
- A4 classification counts (number-lines): {'restated': 32, 'footnote': 149, 'UNKNOWN': 1}; unlabeled removals 0
- A4 UNKNOWN lines: 0 (full context in results/limitation-1963_numlines.json):
- A5 LOOKAHEAD_LINES=40, longest actually used=1, restated >2 pages away: []
- A6 scanner iterations: 3 of the A6 maximum (see ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.

## A1 page-joining evidence (first 5 page-spanning records)

- page-spanning records: 8
- section 2 pages p3-p4
  - join 3->3 removed between: ['boilerplate']
  - before: ...'2. Definitions.—In this Act, unless the context otherwise requires,—\n(a) “applicant” includes—'
  - after: '(i) a petitioner;\n(ii) any person from or through whom an applicant derives his right to apply;\n(iii) any person whose estate is represented'
  - join 3->4 removed between: ['footnote', 'page_number']
  - before: ...'f derives his right to sue;\n(ii) any person whose estate is represented by the plaintiff as executor, administrator or other\nrepresentative;'
  - after: '(j) “period of limitation” means the period of limitation prescribed for any suit, appeal or\napplication by the Schedule, and “prescribed pe'
- section 6 pages p4-p5
  - join 4->5 removed between: ['page_number']
  - before: ...'after the disability has\nceased, as would otherwise have been allowed from the time specified there for in the third column of the\nSchedule.'
  - after: '(2) Where such person is, at the time from which the prescribed period is to be reckoned, affected by\ntwo such disabilities, or where, befor'
- section 11 pages p5-p6
  - join 5->6 removed between: ['page_number']
  - before: ...'try shall be a\ndefence to a suit instituted in the said territories on a contract entered into in that State on in a foreign\ncountry unless—'
  - after: '(a) the rule has extinguished the contract; and\n(b) the parties were domiciled in that State or in the foreign country during the period pre'
- section 14 pages p6-p7
  - join 6->7 removed between: ['footnote', 'page_number']
  - before: ...'a former civil proceeding was pending, the day on which\nthat proceeding was instituted and the day on which it ended shall both be counted;'
  - after: '(b) a plaintiff or an applicant resisting an appeal shall be deemed to be prosecuting a proceeding;\n(c) misjoinder of parties or of causes o'
- section 17 pages p7-p8
  - join 7->8 removed between: ['page_number']
  - before: ...'mistake; or\n(d) where any document necessary to establish the right of the plaintiff or applicant has been\nfraudulently concealed from him,'
  - after: 'the period of limitation shall not begin to run until the plaintiff or applicant has discovered the fraud or\nthe mistake or could, with reas'
  - join 8->8 removed between: ['boilerplate']
  - before: ...'s not a party to the concealment and, did not at the time of purchase know, or have\nreason to believe, that the document had been concealed.'
  - after: '(2) Where a judgment-debtor has, by fraud or force, prevented the execution of a decree or order\nwithin the period of limitation, the court'

## A2 verbatim / removal labels

- A2 PRIMARY fragment windows: 99.7959% (threshold 99%)
- DIAGNOSTIC whole-record windows: 97.992%
- DIAGNOSTIC cleaned-lines-in-raw: 100.0%
- removal label counts: {'boilerplate': 9, 'footnote': 9, 'page_number': 9, 'header': 9}; unlabeled removals: 0 (unlabeled = FAIL)
- 20-line removed sample printed with seed 20261012: see results/limitation-1963_step6_validate.log

## A3 statuses

- status counts: {'in_force': 30, 'omitted': 2}
- R-form (omitted) sections: 28, 32

## 20 random records (seed 20261011)

### 1. limitation-1963:s:32:0
- number='32', title='Repeal', chapter=None, pages 11-11, status=omitted, chars=117, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 32. [Repeal.]—Rep. by Repealing and Amending Act, 1974 (56 of 1974), s. 2 and the First Schedule (w.e.f. 20-12-1974)....

### 2. limitation-1963:s:12:0
- number='12', title='Exclusion of time in legal proceedings', chapter=None, pages 6-6, status=in_force, chars=1175, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=1
- text: 12. Exclusion of time in legal proceedings.—(1) In computing the period of limitation for any suit, appeal or application, the day from which such period is to be reckoned, shall be excluded. (2) In computing the period of limitation for an...

### 3. limitation-1963:s:16:0
- number='16', title='Effect of death on or before the accrual of the right to sue', chapter=None, pages 7-7, status=in_force, chars=1107, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 16. Effect of death on or before the accrual of the right to sue.—(1) Where a person who would, if he were living, have a right to institute a suit or make an application dies before the right accrues, or where a right to institute a suit o...

### 4. limitation-1963:s:11:0
- number='11', title='Suits on contracts entered into outside the territories to which the Act extends', chapter=None, pages 5-6, status=in_force, chars=694, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 11. Suits on contracts entered into outside the territories to which the Act extends.—(1) Suits instituted in the territories to which this Act extends on contracts entered into in the State of Jammu and Kashmir or in a foreign country shal...

### 5. limitation-1963:s:9:0
- number='9', title='Continuous running of time', chapter=None, pages 5-5, status=in_force, chars=389, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 9. Continuous running of time.—Where once time has begun to run, no subsequent disability or inability to institute a suit or make an application stops it: Provided that, where letters of administration to the estate of a creditor have been...

### 6. limitation-1963:s:2:0
- number='2', title='Definitions', chapter=None, pages 3-4, status=in_force, chars=2217, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 2. Definitions.—In this Act, unless the context otherwise requires,— (a) “applicant” includes— (i) a petitioner; (ii) any person from or through whom an applicant derives his right to apply; (iii) any person whose estate is represented by t...

### 7. limitation-1963:s:27:0
- number='27', title='Extinguishment of right to property', chapter=None, pages 10-10, status=in_force, chars=209, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 27. Extinguishment of right to property.—At the determination of the period hereby limited to any person for instituting a suit for possession of any property, his right to such property shall be extinguished....

### 8. limitation-1963:s:31:0
- number='31', title='Provisions as to barred or pending suits, etc', chapter=None, pages 11-11, status=in_force, chars=416, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 31. Provisions as to barred or pending suits, etc.—Nothing in this Act shall,— (a) enable any suit, appeal or application to be instituted, preferred or made, for which the period of limitation prescribed by the Indian Limitation Act, 1908 ...

### 9. limitation-1963:s:30:0
- number='30', title='Provision for suits, etc., for which the prescribed period is shorter than the period prescribed by the Indian Limitation Act, 1908', chapter=None, pages 10-11, status=in_force, chars=3533, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=2
- text: 30. Provision for suits, etc., for which the prescribed period is shorter than the period prescribed by the Indian Limitation Act, 1908.—Notwithstanding anything contained in this Act,— (a) any suit for which the period of limitation is sho...

### 10. limitation-1963:s:26:0
- number='26', title='Exclusion in favour of reversioner of serivent tenement', chapter=None, pages 10-10, status=in_force, chars=611, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 26. Exclusion in favour of reversioner of serivent tenement.—Where any land or water upon, over or from, which any easement has been enjoyed or derived has been held under or by virtue of any interest for life or in terms of years exceeding...

### 11. limitation-1963:s:1:0
- number='1', title='Short title, extent and commencement', chapter=None, pages 3-3, status=in_force, chars=260, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 1. Short title, extent and commencement.—(1) This Act may be called the Limitation Act, 1963. (2) It extends to the whole of India 1***. (3) It shall come into force on such date2 as the Central Government may, by notification in the Offici...

### 12. limitation-1963:s:25:0
- number='25', title='Acquisition of easements by prescription', chapter=None, pages 9-10, status=in_force, chars=1444, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text:  25. Acquisition of easements by prescription.—(1) Where the access and use of light or air to and for any building have been peaceably enjoyed therewith as an easement, and as of right, without interruption, and for twenty years, and where...

### 13. limitation-1963:s:7:0
- number='7', title='Disability of one of several persons', chapter=None, pages 5-5, status=in_force, chars=939, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text:  7. Disability of one of several persons.—Where one of several persons jointly entitled to institute a suit or make an application for the execution of a decree is under any such disability, and a discharge can be given without the concurre...

### 14. limitation-1963:s:17:0
- number='17', title='Effect of fraud or mistake', chapter=None, pages 7-8, status=in_force, chars=2279, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 17. Effect of fraud or mistake.—(1) Where, in the case of any suit or application for which a period of limitation is prescribed by this Act,— (a) the suit or application is based upon the fraud of the defendant or respondent or his agent; ...

### 15. limitation-1963:s:5:0
- number='5', title='Extension of prescribed period in certain cases', chapter=None, pages 4-4, status=in_force, chars=635, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 5. Extension of prescribed period in certain cases.—Any appeal or any application, other than an application under any of the provisions of Order XXI of the Code of Civil Procedure, 1908 (5 of 1908), may be admitted after the prescribed per...

### 16. limitation-1963:s:24:0
- number='24', title='Computation of time mentioned in instruments', chapter=None, pages 9-9, status=in_force, chars=163, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 24. Computation of time mentioned in instruments.—All instruments shall for the purposes of this Act be deemed to be made with reference to the Gregorian calendar....

### 17. limitation-1963:s:22:0
- number='22', title='Continuing breaches and torts', chapter=None, pages 9-9, status=in_force, chars=257, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 22. Continuing breaches and torts.—In the case of a continuing breach of contract or in the case of a continuing tort, a fresh period of limitation begins to run at every moment of the time during which the breach or the tort, as the case m...

### 18. limitation-1963:s:19:0
- number='19', title='Effect of payment on account of debt or of interest on legacy', chapter=None, pages 8-9, status=in_force, chars=856, parts 1/1
- has: proviso=True, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 19. Effect of payment on account of debt or of interest on legacy.—Where payment on account of a debt or of interest on a legacy is made before the expiration of the prescribed period by the person liable to pay the debt or legacy or by his...

### 19. limitation-1963:s:4:0
- number='4', title='Expiry of prescribed period when court is closed', chapter=None, pages 4-4, status=in_force, chars=438, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 4. Expiry of prescribed period when court is closed.—Where the prescribed period for any suit, appeal or application expires on a day when the court is closed, the suit, appeal or application may be instituted, preferred or made on the day ...

### 20. limitation-1963:s:14:0
- number='14', title='Exclusion of time of proceeding bona fide in court without jurisdiction', chapter=None, pages 6-7, status=in_force, chars=1857, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 14. Exclusion of time of proceeding bona fide in court without jurisdiction.—(1) In computing the period of limitation for any suit the time during which the plaintiff has been prosecuting with due diligence another civil proceeding, whethe...

## Consumer Protection 2019 (paused at checkpoint 1)

- registry entry and source PDF present; inspection NOT run per instruction.
- when resumed, G2 must run in ToC mode: every expected section from the ToC needs >=1 record (100% required; missing/extra listed).

## Block-order note

- pages where raw extraction order differs from (y,x) reading order: 24/24 (total counter: {'pages': 1565, 'diff_pages': 1565}); (y,x) order kept. G6 evidence: see ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw reference).

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

- output/limitation-1963.jsonl (32 records)
- results/limitation-1963_gates.json, _clean.json, _segments.json, _flags.json, _assembly.json, _markers.json, _numlines.json, _expected.json, _expected_meta.json, _toc_meta.json
- results/limitation-1963_step2_inspect.log ... _limitation-1963_step7_report.log (one per step)
- results/pilot_report.md (this file)
