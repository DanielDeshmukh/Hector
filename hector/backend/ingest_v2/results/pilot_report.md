# HECTOR ingest_v2 pilot report - The Bharatiya Sakshya Adhiniyam, 2023 (bsa-2023)

- source: sources/bsa-2023.pdf (54 pages as scanned)
- records written: 172 (output/bsa-2023.jsonl)
- gate summary: all gates OK
- seeds: G1 middle pages 20261010; A2 removed-line sample 20261012; step7 record sample 20261011
- external anchor: max plain section = 170 (expected 511) -> WARNING

## Gate table (G1-G9)

| Gate | Status | Evidence |
|---|---|---|
| G1 | **PASS** | page1 act_name=True, year=True; middle pages 15, 21, 25, 35, 39 all have markers (seed 20261010) |
| G2 | **PASS** | mode=toc; expected 170 sections; records 172; missing 0 []; extra 0 []; external anchor max_plain=170 vs 511 -> WARNING |
| G3 | **PASS** | part-0 records 170; prefix stripping needed 0; failures 0 |
| G4 | **PASS** | page-number lines 0; hyphen breaks 0; boilerplate 0; repeated>=30% pages 0 |
| G5 | **PASS** | records 172; duplicates []; empty []; non-nullable problems 0 |
| G6 | **PASS** | PRIMARY fragment windows 2384 total, 99.8322% found (>=99% required; reference get_text('text', sort=True)); DIAG whole-record 98.4873%, DIAG lines 100.0%; failures 4 |
| G7 | **PASS** | parent order matches marker order; parts consistent; problems [] |
| G8 | **PASS** | limit 3000 chars; longest 6256; unflagged overs 0; flagged 6 |
| G9 | **PASS** | detected 2 = attached 0 + unattached 2; accounting_ok=True; records containing footnote lines 0 |

Notes:
- G2 is the ToC cross-check: every section listed in the book's Arrangement of Sections must have at least one record (100% coverage required; missing and extra numbers listed in gate evidence). Range markers count as covering their printed span; the external anchor 511 is reported separately above.
- G6 PRIMARY uses the A2 fragment-window definition; the whole-record window check and the cleaned-line check are DIAGNOSTIC (A2).

## Coverage / sequence detail (A4, A5, A6)

- accepted markers: 170; forms: {'M': 0, 'D': 170, 'R': 0}
- lettered/other non-plain numbers: 0 entries ()
- rejected candidates: 6
- gaps: []
- A4 classification counts (number-lines): {'restated': 170, 'footnote': 1, 'UNKNOWN': 5}; unlabeled removals 0
- A4 UNKNOWN lines: 5 (full context in results/bsa-2023_numlines.json):
  - line 2011 p54: '2. The experience of seven decades of Indian democracy calls for comprehensive review of our'
  - line 2017 p54: '3. Accordingly, a Bill, namely, the Bharatiya Sakshya Bill, 2023 was introduced in Lok Sabha on'
  - line 2025 p54: '4. The proposed legislation, inter alia, provides as under:-'
  - line 2038 p54: '5. The Notes on Clauses explain the various provisions of the Bill.'
  - line 2039 p54: '6. The Bill seeks to achieve the above objectives.'
- A5 LOOKAHEAD_LINES=40, longest actually used=1, restated >2 pages away: []
- A6 scanner iterations: 3 of the A6 maximum (see ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.

## A1 page-joining evidence (first 5 page-spanning records)

- page-spanning records: 30
- section 2 pages p10-p12
  - join 10->10 removed between: ['boilerplate']
  - before: ...'hose\nmeans, intended to be used, or which may be used, for the purpose of recording that matter and\nincludes electronic and digital records.'
  - after: '(i) A writing is a document.\n(ii) Words printed, lithographed or photographed are documents.\n(iii) A map or plan is a document.\n(iv) An insc'
  - join 10->11 removed between: ['footnote', 'page_number']
  - before: ...'messages, websites, locational evidence and voice mail messages stored on digital devices are\ndocuments;\n(e) “evidence” means and includes—'
  - after: '(i) all statements including statements given electronically which the Court permits or\nrequires to be made before it by witnesses in relati'
  - join 11->11 removed between: ['boilerplate']
  - before: ...'tate of things, or relation of things, capable of being perceived by the\nsenses;\n(ii) any mental condition of which any person is conscious.'
  - after: '(i) That there are certain objects arranged in a certain order in a certain place, is a fact.\n(ii) That a person heard or saw something, is'
  - join 11->11 removed between: ['boilerplate']
  - before: ...'t there are certain objects arranged in a certain order in a certain place, is a fact.\n(ii) That a person heard or saw something, is a fact.'
  - after: '(iii) That a person said certain words, is a fact.\n(iv) That a person holds a certain opinion, has a certain intention, acts in good faith,'
  - join 11->11 removed between: ['boilerplate']
  - before: ...'ng\nto Civil Procedure, any Court records an issue of fact, the fact to be asserted or denied in the\nanswer to such issue is a fact in issue.'
  - after: "A is accused of the murder of B. At his trial, the following facts may be in issue:—\n(i) That A caused B's death.\n(ii) That A intended to ca"
  - join 11->12 removed between: ['page_number']
  - before: ...'r when it is connected with the other in\nany of the ways referred to in the provisions of this Adhiniyam relating to the relevancy of facts;'
  - after: '(l) “shall presume”.—Whenever it is directed by this Adhiniyam that the Court shall presume\na fact, it shall regard such fact as proved, unl'
- section 5 pages p12-p13
  - join 12->13 removed between: ['boilerplate', 'page_number']
  - before: ...'onstitute the state of things under which they happened, or which afforded an opportunity for their\noccurrence or transaction, are relevant.'
  - after: '(a) The question is, whether A robbed B. The facts that, shortly before the robbery, B went to a fair\nwith money in his possession, and that'
- section 6 pages p13-p14
  - join 13->13 removed between: ['boilerplate']
  - before: ...'evant, if such conduct\ninfluences or is influenced by any fact in issue or relevant fact, and whether it was previous or subsequent\nthereto.'
  - after: 'Explanation 1.—The word “conduct” in this section does not include statements, unless those\nstatements accompany and explain acts other than'
  - join 13->13 removed between: ['boilerplate']
  - before: ...'en the conduct of any person is relevant, any statement made to him or in his\npresence and hearing, which affects such conduct, is relevant.'
  - after: '(a) A is tried for the murder of B. The facts that A murdered C, that B knew that A had murdered C,\nand that B had tried to extort money fro'
  - join 13->14 removed between: ['page_number']
  - before: ...'earing—“I advise you not to trust A, for he owes B ten\nthousand rupees”, and that A went away without making any answer, are relevant facts.'
  - after: '(h) The question is, whether A committed a crime. The fact that A absconded, after receiving a letter,\nwarning A that inquiry was being made'
- section 8 pages p14-p15
  - join 14->15 removed between: ['page_number']
  - before: ...'t entertained by any one of them, is a\nrelevant fact as against each of the persons believed to be so conspiring, as well for the purpose of'
  - after: 'proving the existence of the conspiracy as for the purpose of showing that any such person was a party to\nit.'
  - join 15->15 removed between: ['boilerplate']
  - before: ...'proving the existence of the conspiracy as for the purpose of showing that any such person was a party to\nit.'
  - after: 'Reasonable ground exists for believing that A has joined in a conspiracy to wage war against the\nState.\nThe facts that B procured arms in Eu'
- section 12 pages p15-p17
  - join 15->16 removed between: ['page_number']
  - before: ...'ate of body or bodily feeling,\nare relevant, when the existence of any such state of mind or body or bodily feeling is in issue or relevant.'
  - after: 'Explanation 1.—A fact relevant as showing the existence of a relevant state of mind must show that\nthe state of mind exists, not generally,'
  - join 16->16 removed between: ['boilerplate']
  - before: ...'accused of an offence is relevant within the meaning of this section, the previous\nconviction of such person shall also be a relevant fact.'
  - after: '(a) A is accused of receiving stolen goods knowing them to be stolen. It is proved that he was in\npossession of a particular stolen article.'
  - join 16->16 removed between: ['boilerplate']
  - before: ...'A had been previously\nconvicted of delivering to another person as genuine a counterfeit currency knowing it to be counterfeit is\nrelevant.'
  - after: "(c) A sues B for damage done by a dog of B's, which B knew to be ferocious. The fact that the dog\nhad previously bitten X, Y and Z, and that"
  - join 16->17 removed between: ['page_number']
  - before: ...'cruelty towards B, his wife. Expressions of their\nfeeling towards each other shortly before or after the alleged cruelty are relevant facts.'
  - after: "(l) The question is, whether A's death was caused by poison. Statements made by A during his illness\nas to his symptoms are relevant facts."

## A2 verbatim / removal labels

- A2 PRIMARY fragment windows: 99.8322% (threshold 99%)
- DIAGNOSTIC whole-record windows: 98.4873%
- DIAGNOSTIC cleaned-lines-in-raw: 100.0%
- removal label counts: {'boilerplate': 104, 'footnote': 2, 'page_number': 45, 'header': 34}; unlabeled removals: 0 (unlabeled = FAIL)
- 20-line removed sample printed with seed 20261012: see results/bsa-2023_step6_validate.log

## A3 statuses

- status counts: {'in_force': 172}
- R-form (omitted) sections: 

## 20 random records (seed 20261011)

### 1. bsa-2023:s:124:0
- number='124', title='Who may testify', chapter='CHAPTER IX - OF WITNESSES', pages 43-43, status=in_force, chars=517, parts 1/1
- has: proviso=False, explanation=True, exception=False, illustration=False, amendment_notes=0
- text: 124. Who may testify.—All persons shall be competent to testify unless the Court considers that they are prevented from understanding the questions put to them, or from giving rational answers to those questions, by tender years, extreme ol...

### 2. bsa-2023:s:88:0
- number='88', title='Presumption as to certified copies of foreign judicial records', chapter='CHAPTER V - OF DOCUMENTARY EVIDENCE', pages 34-35, status=in_force, chars=817, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 88. Presumption as to certified copies of foreign judicial records.—(1) The Court may presume that any document purporting to be a certified copy of any judicial record of any country beyond India is genuine and accurate, if the document pu...

### 3. bsa-2023:s:125:0
- number='125', title='Witness unable to communicate verbally', chapter='CHAPTER IX - OF WITNESSES', pages 43-43, status=in_force, chars=519, parts 1/1
- has: proviso=True, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 125. Witness unable to communicate verbally.—A witness who is unable to speak may give his evidence in any other manner in which he can make it intelligible, as by writing or by signs; but such writing must be written and the signs made in ...

### 4. bsa-2023:s:86:0
- number='86', title='Presumption as to electronic records and electronic signatures', chapter='CHAPTER V - OF DOCUMENTARY EVIDENCE', pages 34-34, status=in_force, chars=785, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 86. Presumption as to electronic records and electronic signatures.—(1) In any proceeding involving a secure electronic record, the Court shall presume unless contrary is proved, that the secure electronic record has not been altered since ...

### 5. bsa-2023:s:71:0
- number='71', title='Proof of document not required by law to be attested', chapter='CHAPTER V - OF DOCUMENTARY EVIDENCE', pages 32-32, status=in_force, chars=152, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 71. Proof of document not required by law to be attested.—An attested document not required by law to be attested may be proved as if it was unattested....

### 6. bsa-2023:s:15:0
- number='15', title='Admission defined', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 17-17, status=in_force, chars=268, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 15. Admission defined.—An admission is a statement, oral or documentary or contained in electronic form, which suggests any inference as to any fact in issue or relevant fact, and which is made by any of the persons, and under the circumsta...

### 7. bsa-2023:s:11:0
- number='11', title='Facts relevant when right or custom is in question', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 15-15, status=in_force, chars=860, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 11. Facts relevant when right or custom is in question.—Where the question is as to the existence of any right or custom, the following facts are relevant— (a) any transaction by which the right or custom in question was created, claimed, m...

### 8. bsa-2023:s:91:0
- number='91', title='Presumption as to due execution, etc., of documents not produced', chapter='CHAPTER V - OF DOCUMENTARY EVIDENCE', pages 35-35, status=in_force, chars=233, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 91. Presumption as to due execution, etc., of documents not produced.—The Court shall presume that every document, called for and not produced after notice to produce, was attested, stamped and executed in the manner required by law....

### 9. bsa-2023:s:121:0
- number='121', title='Estoppel', chapter='CHAPTER VIII - ESTOPPEL', pages 42-42, status=in_force, chars=664, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 121. Estoppel.—When one person has, by his declaration, act or omission, intentionally caused or permitted another person to believe a thing to be true and to act upon such belief, neither he nor his representative shall be allowed, in any ...

### 10. bsa-2023:s:10:0
- number='10', title='Facts tending to enable Court to determine amount are relevant in suits for damages', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 15-15, status=in_force, chars=239, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 10. Facts tending to enable Court to determine amount are relevant in suits for damages.—In suits in which damages are claimed, any fact which will enable the Court to determine the amount of damages which ought to be awarded, is relevant....

### 11. bsa-2023:s:4:0
- number='4', title='Relevancy of facts forming part of same transaction', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 12-12, status=in_force, chars=1292, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 4. Relevancy of facts forming part of same transaction.—Facts which, though not in issue, are so connected with a fact in issue or a relevant fact as to form part of the same transaction, are relevant, whether they occurred at the same time...

### 12. bsa-2023:s:170:0
- number='170', title='Repeal and savings', chapter='CHAPTER XII - REPEAL AND SAVINGS', pages 51-54, status=in_force, chars=6256, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 170. Repeal and savings.—(1) The Indian Evidence Act, 1872 (1 of 1872) is hereby repealed. (2) Notwithstanding such repeal, if, immediately before the date on which this Adhiniyam comes into force, there is any application, trial, inquiry, ...

### 13. bsa-2023:s:56:0
- number='56', title='Proof of contents of documents', chapter='CHAPTER V - OF DOCUMENTARY EVIDENCE', pages 28-28, status=in_force, chars=119, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 56. Proof of contents of documents.—The contents of documents may be proved either by primary or by secondary evidence....

### 14. bsa-2023:s:167:0
- number='167', title='Using, as evidence, of document production of which was refused on notice', chapter='CHAPTER X - OF EXAMINATION OF WITNESSES', pages 50-50, status=in_force, chars=606, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 167. Using, as evidence, of document production of which was refused on notice.— When a party refuses to produce a document which he has had notice to produce, he cannot afterwards use the document as evidence without the consent of the oth...

### 15. bsa-2023:s:153:0
- number='153', title='Procedure of Court in case of question being asked without reasonable grounds', chapter='CHAPTER X - OF EXAMINATION OF WITNESSES', pages 48-48, status=in_force, chars=355, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 153. Procedure of Court in case of question being asked without reasonable grounds.—If the Court is of opinion that any such question was asked without reasonable grounds, it may, if it was asked by any advocate, report the circumstances of...

### 16. bsa-2023:s:134:0
- number='134', title='Confidential communication with legal advisers', chapter='CHAPTER IX - OF WITNESSES', pages 44-45, status=in_force, chars=417, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 134. Confidential communication with legal advisers.—No one shall be compelled to disclose to the Court any confidential communication which has taken place between him and his legal adviser, unless he offers himself as a witness, in which ...

### 17. bsa-2023:s:33:0
- number='33', title='What evidence to be given when statement forms part of a conversation, document, electronic record, book or series of letters or papers', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 22-23, status=in_force, chars=778, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 33. What evidence to be given when statement forms part of a conversation, document, electronic record, book or series of letters or papers.—When any statement of which evidence is given forms part of a longer statement, or of a conversatio...

### 18. bsa-2023:s:119:1
- number='119', title='Court may presume existence of certain facts', chapter='CHAPTER VII - OF THE BURDEN OF PROOF', pages 41-42, status=in_force, chars=2264, parts 2/2
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: (2) The Court shall also have regard to such facts as the following, in considering whether such maxims do or do not apply to the particular case before it:— (i) as to Illustration (a)—a shop-keeper has in his bill a marked rupee soon after...

### 19. bsa-2023:s:7:0
- number='7', title='Facts necessary to explain or introduce fact in issue or relevant facts', chapter='CHAPTER II - RELEVANCY OF FACTS', pages 14-14, status=in_force, chars=2391, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 7. Facts necessary to explain or introduce fact in issue or relevant facts.—Facts necessary to explain or introduce a fact in issue or relevant fact, or which support or rebut an inference suggested by a fact in issue or a relevant fact, or...

### 20. bsa-2023:s:1:0
- number='1', title='Short title, application and commencement', chapter='CHAPTER I - PRELIMINARY', pages 10-10, status=in_force, chars=428, parts 1/1
- has: proviso=False, explanation=False, exception=False, illustration=False, amendment_notes=0
- text: 1. Short title, application and commencement.–– (1) This Act may be called the Bharatiya Sakshya Adhiniyam, 2023. (2) It applies to all judicial proceedings in or before any Court, including Courts-martial, but not to affidavits presented t...

## Consumer Protection 2019 (paused at checkpoint 1)

- registry entry and source PDF present; inspection NOT run per instruction.
- when resumed, G2 must run in ToC mode: every expected section from the ToC needs >=1 record (100% required; missing/extra listed).

## Block-order note

- pages where raw extraction order differs from (y,x) reading order: 54/54 (total counter: {'pages': 567, 'diff_pages': 567}); (y,x) order kept. G6 evidence: see ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw reference).

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

- output/bsa-2023.jsonl (172 records)
- results/bsa-2023_gates.json, _clean.json, _segments.json, _flags.json, _assembly.json, _markers.json, _numlines.json, _expected.json, _expected_meta.json, _toc_meta.json
- results/bsa-2023_step2_inspect.log ... _bsa-2023_step7_report.log (one per step)
- results/pilot_report.md (this file)
