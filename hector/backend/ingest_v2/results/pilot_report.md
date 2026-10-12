# HECTOR ingest_v2 pilot report - The Code of Civil Procedure, 1908 (cpc-1908)

- source: sources/cpc-1908.pdf (347 pages as scanned)
- records written: 174 (output/cpc-1908.jsonl)
- gate summary: all gates OK
- seeds: G1 middle pages 20261010; A2 removed-line sample 20261012; step7 record sample 20261011
- external anchor: max plain section = 158 (expected 511) -> WARNING

## Gate table (G1-G9)

| Gate | Status | Evidence |
|---|---|---|
| G1 | **PASS** | page1 act_name=True, year=True; middle pages 97, 146, 152, 176, 256 all have markers (seed 20261010) |
| G2 | **PASS** | mode=toc; expected 171 sections; records 174; missing 0 []; extra 0 []; external anchor max_plain=158 vs 511 -> WARNING |
| G3 | **PASS** | part-0 records 171; prefix stripping needed 0; failures 0 |
| G4 | **PASS** | page-number lines 0; hyphen breaks 0; boilerplate 0; repeated>=30% pages 0 |
| G5 | **PASS** | records 174; duplicates []; empty []; non-nullable problems 0 |
| G6 | **PASS** | PRIMARY fragment windows 2599 total, 99.7691% found (>=99% required; reference get_text('text', sort=True)); DIAG whole-record 97.8699%, DIAG lines 100.0%; failures 6 |
| G7 | **PASS** | parent order matches marker order; parts consistent; problems [] |
| G8 | **PASS** | limit 3000 chars; longest 14222; unflagged overs 0; flagged 6 |
| G9 | **PASS** | detected 7001 = attached 264 + unattached 6737; accounting_ok=True; records containing footnote lines 0 |

Notes:
- G2 is the ToC cross-check: every section listed in the book's Arrangement of Sections must have at least one record (100% coverage required; missing and extra numbers listed in gate evidence). Range markers count as covering their printed span; the external anchor 511 is reported separately above.
- G6 PRIMARY uses the A2 fragment-window definition; the whole-record window check and the cleaned-line check are DIAGNOSTIC (A2).

## Coverage / sequence detail (A4, A5, A6)

- accepted markers: 171; forms: {'M': 1, 'D': 158, 'R': 12}
- lettered/other non-plain numbers: 13 entries (21A, 35A, 35B, 44A, 87A, 87B, 99A, 100A, 111A, 135A, 148A, 153A...)
- rejected candidates: 1917
- gaps: []
- A4 classification counts (number-lines): {'restated': 171, 'footnote': 1911, 'UNKNOWN': 6, 'margin': 1}; unlabeled removals 0
- A4 UNKNOWN lines: 3 (full context in results/cpc-1908_numlines.json):
  - line 1970 p72: '115. Revision.—The High Court, in cases arising out of original suits or other proceedings of the'
  - line 1995 p73: '3. Saving.—The amendment made by this Act shall not affect the validity, invalidity, effect  or'
  - line 2003 p73: '115. Revision.—(1) The High Court, in cases arising out of original suits or other proceedings of the'
- A5 LOOKAHEAD_LINES=40, longest actually used=23, restated >2 pages away: []
- A6 scanner iterations: 3 of the A6 maximum (see ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.

## A1 page-joining evidence (first 5 page-spanning records)

- page-spanning records: 34
- section 1 pages p34-p35
  - join 34->35 removed between: ['boilerplate', 'footnote', 'page_number']
  - before: ...'and extent.—(1) This Act may be cited as the Code of Civil\nProcedure, 1908.\n(2) It shall come into force on the first day of January, 1909.'
  - after: '(3) It extends to the whole of India except—\n2*\n       *\n              *\n       *\n    *\n(b) the State of Nagaland and the tribal areas:\nProv'
- section 2 pages p35-p37
  - join 35->35 removed between: ['boilerplate']
  - before: ...'2. Definitions.—In this Act, unless there is anything repugnant in the subject or context,—\n       (1) “Code” includes rules;'
  - after: '(2) “decree” means the formal expression of an adjudication which, so far as regards the Court\nexpressing it, conclusively determines the ri'
  - join 35->36 removed between: ['footnote', 'page_number']
  - before: ...'3 and 87A, means the territory\nof India excluding the State of Jammu and Kashmir;]\n(8) “Judge” means the presiding officer of a Civil Court;'
  - after: '(9) “judgment” means the statement given by the Judge of the grounds of a decree or order;\n(10) “judgment-debtor” means any person ag'
  - join 36->36 removed between: ['boilerplate']
  - before: ...'plead for another in Court, and includes an\nadvocate, a vakil and an attorney of a High Court;\n(16) “prescribed” means prescribed by rules;'
  - after: '(17) “public officer” means a person falling under any of the following descriptions, namely:—\n(a) every Judge;\n(b) every member of  1[an Al'
  - join 36->37 removed between: ['footnote', 'page_number']
  - before: ...'eemed to include stock, debenture stock, debentures or\nbonds; and\n(20) “signed”, save in the case of a judgment or decree, includes stamped.'
  - after: '*\n*\n*\n*'
- section 9 pages p38-p39
  - join 38->38 removed between: ['boilerplate']
  - before: ...'ned) have jurisdiction to try all suits of a civil nature excepting suits of which their cognizance is\neither expressly or impliedly barred.'
  - after: 'Explanation I].—A suit in which the right to property or to an office is contested is a suit of a civil\nnature, notwithstanding that such ri'
  - join 38->38 removed between: ['header']
  - before: ...'er or not any fees are attached\nto the office referred to in Explanation I or whether or not such office is attached to a particular place.]'
  - after: 'Maharashtra.—\nSection 9A of the Code of Civil Procedure, 1908, in its application to the State of Maharashtra\n(hereinafter referred to as “t'
  - join 38->39 removed between: ['footnote', 'page_number']
  - before: ...'ion is pending before a\nrevisional Court, on the date of commencement of the Amendment Act, such revisional proceedings shall\nstand abated :'
  - after: 'Provided that, where a decree in such suit is appealed from any error, defect or irregularity in the order\nupholding jurisdiction shall be t'
  - join 39->39 removed between: ['boilerplate']
  - before: ...'and the Court shall, at the time of deciding the application in which such an\norder is made, either confirm or vacate or modify such order.'
  - after: 'Vide Maharashtra Act 61 of 2018, sec. 3.]\nMaharashtra.—\nIn section 3 of the Code of Civil Procedure (Maharashtra Amendment) Act, 2018, for c'
- section 11 pages p39-p40
  - join 39->40 removed between: ['footnote', 'page_number']
  - before: ...'try\nsuch subsequent suit or the suit in which such issue has been subsequently raised, and has been heard and\nfinally decided by such Court.'
  - after: 'Explanation I.—The expression “former suit” shall denote a suit which has been decided prior to a suit\nin question whether or not it was ins'
  - join 40->40 removed between: ['boilerplate']
  - before: ...'a\nproceeding for the execution of the decree, question arising in such proceeding and a former proceeding for the\nexecution of that decree.'
  - after: 'Explanation VIII.—An issue heard and finally decided by a Court of limited jurisdiction, competent to\ndecide such issue, shall operate as re'
- section 16 pages p40-p41
  - join 40->41 removed between: ['footnote', 'page_number']
  - before: ...'by any law, suits—\n(a) for the recovery of immovable property with or without rent or profits,\n(b) for the partition of immovable property,'
  - after: '(c)  for foreclosure, sale or redemption in the case of a mortgage of or charge upon immovable\nproperty,\n(d) or the determination of any oth'

## A2 verbatim / removal labels

- A2 PRIMARY fragment windows: 99.7691% (threshold 99%)
- DIAGNOSTIC whole-record windows: 97.8699%
- DIAGNOSTIC cleaned-lines-in-raw: 100.0%
- removal label counts: {'boilerplate': 52, 'footnote': 318, 'page_number': 52, 'header': 37, 'separator': 2}; unlabeled removals: 0 (unlabeled = FAIL)
- 20-line removed sample printed with seed 20261012: see results/cpc-1908_step6_validate.log

## A3 statuses

- status counts: {'in_force': 162, 'omitted': 12}
- R-form (omitted) sections: 110, 111, 111A, 154, 155, 156, 48, 66, 69, 70, 71, 72

## 20 random records (seed 20261011)

### 1. cpc-1908:s:114:0
- number='114', title='Review', chapter=None, pages 71-71, status=in_force, chars=480, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 114. Review.—Subject as aforesaid, any person considering himself aggrieved— (a) by a decree or order from which an appeal is allowed by this Code, but from which no appeal has been preferred, (b) by a decree or order from which no appeal i...

### 2. cpc-1908:s:83:0
- number='83', title='When aliens may sue', chapter=None, pages 63-63, status=in_force, chars=656, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 83. When aliens may sue.—Alien enemies residing in India with the permission of the Central Government, and alien friends, may sue in any Court otherwise competent to try the suit, as if they were citizens of India, but alien enemies residi...

### 3. cpc-1908:s:115:0
- number='115', title='Revision', chapter=None, pages 71-76, status=in_force, chars=14222, parts 1/1
- has: proviso=True, explanation=True, exception=False, illustration=False, amendment_notes=6
- text: 115. Revision.—4[(1)] The High Court may call for the record of any case which has been decided by any Court subordinate to such High Court and in which no appeal lies thereto, and if such subordinate Court appears— (a) to have exercised a ...

### 4. cpc-1908:s:81:0
- number='81', title='Exemption from arrest and personal appearance', chapter=None, pages 62-62, status=in_force, chars=473, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 81. Exemption from arrest and personal appearance.—In a suit instituted against a public officer in respect of any act purporting to be done by him in his official capacity— (a) the defendant shall not be liable to arrest nor his property t...

### 5. cpc-1908:s:66:0
- number='66', title='Suit against purchaser not maintainable on ground of purchase being on behalf of plaintiff', chapter=None, pages 59-59, status=omitted, chars=155, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 66. [Suit against purchaser not maintainable on ground of purchase being on behalf of plaintiff.]— Rep. by Act, 1988 (45 of 1988), s. 7 (w.e.f. 19-5-1988)....

### 6. cpc-1908:s:15:0
- number='15', title='Court in which suits to be instituted', chapter=None, pages 40-40, status=in_force, chars=127, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 15. Court in which suits to be instituted.—Every suit shall be instituted in the Court of the lowest grade competent to try it....

### 7. cpc-1908:s:11:0
- number='11', title='Res judicata', chapter=None, pages 39-40, status=in_force, chars=2317, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=1
- text: 11. Res judicata.—No Court shall try any suit or issue in which the matter directly and substantially in issue has been directly and substantially in issue in a former suit between the same parties, or between parties under whom they or any...

### 8. cpc-1908:s:86:0
- number='86', title='Suits against foreign Rulers, Ambassadors and Envoys', chapter=None, pages 63-64, status=in_force, chars=2698, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=11
- text: 86. Suits against foreign Rulers, Ambassadors and Envoys.—(1) No. 2*** foreign State may be sued in any Court otherwise competent to try the suit except with the consent of the Central Government certified in writing by a Secretary to that ...

### 9. cpc-1908:s:111a:0
- number='111A', title='Appeals to Federal Court', chapter=None, pages 71-71, status=omitted, chars=106, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=2
- text: 111A. [Appeals to Federal Court] Rep. by the Federal Court Act, 1941 (21 of 1941), s. 2 (w.e.f. 1-9-1942)....

### 10. cpc-1908:s:10:0
- number='10', title='Stay of suit', chapter=None, pages 39-39, status=in_force, chars=723, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=4
- text: 10. Stay of suit.—No Court shall proceed with the trial of any suit in which the matter in issue is also directly and substantially in issue in a previously instituted suit between the same parties, or between parties under whom they or any...

### 11. cpc-1908:s:4:0
- number='4', title='Savings', chapter=None, pages 37-37, status=in_force, chars=668, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 4. Savings.—(1) In the absence of any specific provision to the contrary, nothing in this Code shall be deemed to limit or otherwise affect any special or local law now in force or any special jurisdiction or power conferred, or any special...

### 12. cpc-1908:s:156:0
- number='156', title='Repeals', chapter=None, pages 84-84, status=omitted, chars=99, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 156. [Repeals.] Rep. by the Second Repealing and Amending Act, 1914 (17 of 1914), s. 3 and Sch. II....

### 13. cpc-1908:s:50:0
- number='50', title='Legal representative', chapter=None, pages 53-53, status=in_force, chars=687, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 50. Legal representative.—(1) Where a judgment-debtor dies before the decree has been fully satisfied, the holder of the decree may apply to the Court which passed it to execute the same against the legal representative of the deceased. (2)...

### 14. cpc-1908:s:153b:0
- number='153B', title='Place of trial to be deemed to be open Court', chapter=None, pages 84-84, status=in_force, chars=531, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 153B. Place of trial to be deemed to be open Court.—The place in which any Civil Court is held for the purpose of trying any suit shall be deemed to be an open Court, to which the public generally may have access so far as the same can conv...

### 15. cpc-1908:s:142:0
- number='142', title='Orders and notices to be in writing', chapter=None, pages 82-82, status=in_force, chars=152, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 142. Orders and notices to be in writing.—All orders and notices served on or given to any person under the provisions of this Code shall be in writing....

### 16. cpc-1908:s:124:0
- number='124', title='Committee to report to High Court', chapter=None, pages 78-78, status=in_force, chars=350, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 124. Committee to report to High Court.—Every Rule Committee shall make a report to the High Court established at the town at which it is constituted on any proposal to annul, alter or add to the rules in the First Schedule or to make new r...

### 17. cpc-1908:s:32:0
- number='32', title='Penalty for default', chapter=None, pages 44-45, status=in_force, chars=407, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 32. Penalty for default.—The Court may compel the attendance of any person to whom a summons has been issued under section 30 and for that purpose may— (a) issue a warrant for his arrest; (b) attach and sell his property; (c) impose a fine ...

### 18. cpc-1908:s:110:0
- number='110', title='Value of subject matters', chapter=None, pages 71-71, status=omitted, chars=130, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=1
- text: 110. [Value of subject matters.] Rep. by the Code of Civil Procedure (Amendment) Act, 1973 (49 of 1973), s. 3 (w.e.f. 29-11-1973)....

### 19. cpc-1908:s:7:0
- number='7', title='Provincial Small Cause Courts', chapter=None, pages 37-37, status=in_force, chars=1044, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=5
- text: 7. Provincial Small Cause Courts.—The following provisions shall not extend to Courts constituted under the Provincial Small Cause Courts Act, 1887 (9 of 1887) 4[or under the Berar Small Cause Courts Law, 1905], or to Courts exercising the ...

### 20. cpc-1908:s:1:0
- number='1', title='Short title, commencement and extent', chapter=None, pages 34-35, status=in_force, chars=1302, parts 1/1
- has: proviso=True, explanation=True, exception=False, illustration=False, amendment_notes=2
- text: 1. Short title, commencement and extent.—(1) This Act may be cited as the Code of Civil Procedure, 1908. (2) It shall come into force on the first day of January, 1909. (3) It extends to the whole of India except— 2*        *               ...

## Consumer Protection 2019 (paused at checkpoint 1)

- registry entry and source PDF present; inspection NOT run per instruction.
- when resumed, G2 must run in ToC mode: every expected section from the ToC needs >=1 record (100% required; missing/extra listed).

## Block-order note

- pages where raw extraction order differs from (y,x) reading order: 347/347 (total counter: {'pages': 1969, 'diff_pages': 1964}); (y,x) order kept. G6 evidence: see ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw reference).

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

- output/cpc-1908.jsonl (174 records)
- results/cpc-1908_gates.json, _clean.json, _segments.json, _flags.json, _assembly.json, _markers.json, _numlines.json, _expected.json, _expected_meta.json, _toc_meta.json
- results/cpc-1908_step2_inspect.log ... _cpc-1908_step7_report.log (one per step)
- results/pilot_report.md (this file)
