export type AnchorKind =
  | "section"
  | "clause"
  | "proviso"
  | "exception"
  | "illustration"
  | "explanation"
  | "schedule";

export interface Part {
  kind: AnchorKind;
  label?: string;
  text: string;
}

export interface Section {
  id: string;
  code: string;
  act: string;
  year: number;
  section: string;
  note: string;
  chapter: string;
  status: "Active" | "Repealed";
  parts: Part[];
  /** correspondence to another indexed section */
  counterpart?: string;
  /** for repealed statutes: which provision now carries the text */
  flag?: "renumbered" | "split" | "replaced" | "retained";
}

export const CORPUS: Section[] = [
  {
    id: "bns-103",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "103",
    note: "Punishment for murder",
    chapter: "Chapter XV · Offences affecting the human life",
    status: "Active",
    counterpart: "ipc-302",
    parts: [
      {
        kind: "section",
        label: "SECTION 103",
        text: "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
      },
    ],
  },
  {
    id: "ipc-302",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "302",
    note: "Punishment for murder",
    chapter: "Chapter XVI · Offences affecting the human life",
    status: "Repealed",
    counterpart: "bns-103",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        label: "SECTION 302",
        text: "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
      },
    ],
  },
  {
    id: "bns-102",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "102",
    note: "Murder",
    chapter: "Chapter XV · Offences affecting the human life",
    status: "Active",
    counterpart: "ipc-300",
    parts: [
      {
        kind: "section",
        text: "Except in the cases hereinafter excepted, culpable homicide is murder,—",
      },
      {
        kind: "clause",
        label: "first",
        text: "if the act by which the death is caused is done with the intention of causing death;",
      },
      {
        kind: "clause",
        label: "secondly",
        text: "if it is done with the intention of causing such bodily injury as the offender knows to be likely to cause death;",
      },
      {
        kind: "clause",
        label: "thirdly",
        text: "if it is done with the intention of causing bodily injury which the offender knows to be sufficient in the ordinary course of nature to cause death;",
      },
      {
        kind: "clause",
        label: "fourthly",
        text: "if the offender does the act known to be so imminently dangerous that it must in all probability cause death…",
      },
      {
        kind: "exception",
        label: "Exception 1",
        text: "Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation…",
      },
      {
        kind: "exception",
        label: "Exception 2",
        text: "Culpable homicide is not murder if the offender, in the exercise in good faith of private defence of person or property, exceeds the power given to him…",
      },
      {
        kind: "exception",
        label: "Exception 3",
        text: "Culpable homicide is not murder if a public servant, acting in the discharge of his duty, exceeds the powers of a public servant…",
      },
      {
        kind: "exception",
        label: "Exception 4",
        text: "Culpable homicide is not murder if the offender, whilst in sudden fight, causes death in the heat of passion without premeditation…",
      },
      {
        kind: "exception",
        label: "Exception 5",
        text: "Culpable homicide is not murder if the person whose death is caused, being above the age of eighteen years, suffers death at the hands of the victim with his own consent…",
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A, on sudden provocation received from B, kills B in the heat of passion. A has committed culpable homicide not amounting to murder.",
      },
    ],
  },
  {
    id: "ipc-300",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "300",
    note: "Murder",
    chapter: "Chapter XVI · Offences affecting the human life",
    status: "Repealed",
    counterpart: "bns-102",
    flag: "retained",
    parts: [
      {
        kind: "section",
        text: "Except in the cases hereinafter excepted, culpable homicide is murder,—",
      },
      {
        kind: "clause",
        label: "first",
        text: "if the act by which the death is caused is done with the intention of causing death;",
      },
      {
        kind: "clause",
        label: "secondly",
        text: "if it is done with the intention of causing such bodily injury as the offender knows to be likely to cause death;",
      },
      {
        kind: "clause",
        label: "thirdly",
        text: "if it is done with the intention of causing bodily injury which the offender knows to be sufficient in the ordinary course of nature to cause death;",
      },
      {
        kind: "clause",
        label: "fourthly",
        text: "if the offender does the act known to be so imminently dangerous that it must in all probability cause death…",
      },
      {
        kind: "exception",
        label: "Exception 1",
        text: "Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation…",
      },
      {
        kind: "exception",
        label: "Exception 2",
        text: "Culpable homicide is not murder if the offender, in the exercise in good faith of private defence of person or property, exceeds the power given to him…",
      },
      {
        kind: "exception",
        label: "Exception 3",
        text: "Culpable homicide is not murder if a public servant, acting in the discharge of his duty, exceeds the powers of a public servant…",
      },
      {
        kind: "exception",
        label: "Exception 4",
        text: "Culpable homicide is not murder if the offender, whilst in sudden fight, causes death in the heat of passion without premeditation…",
      },
      {
        kind: "exception",
        label: "Exception 5",
        text: "Culpable homicide is not murder if the person whose death is caused, being above the age of eighteen years, suffers death at the hands of the victim with his own consent…",
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A, on sudden provocation received from B, kills B in the heat of passion. A has committed culpable homicide not amounting to murder.",
      },
    ],
  },
  {
    id: "bns-104",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "104",
    note: "Punishment for culpable homicide not amounting to murder (intention)",
    chapter: "Chapter XV · Offences affecting the human life",
    status: "Active",
    counterpart: "ipc-304",
    parts: [
      {
        kind: "section",
        text: "Whoever commits culpable homicide not amounting to murder, where the act by which death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death, shall be punished with imprisonment for life, or with imprisonment which may extend to ten years, and shall also be liable to fine.",
      },
    ],
  },
  {
    id: "ipc-304",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "304",
    note: "Punishment for culpable homicide not amounting to murder",
    chapter: "Chapter XVI · Offences affecting the human life",
    status: "Repealed",
    counterpart: "bns-104",
    flag: "split",
    parts: [
      {
        kind: "section",
        text: "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine, if the act by which the death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death,",
      },
      {
        kind: "clause",
        label: "second part",
        text: "and with imprisonment of either description for a term which may extend to ten years, or with fine, or with both, if the act is done with the knowledge that it is likely to cause death, but without any intention to cause death…",
      },
    ],
  },
  {
    id: "bns-316",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "316",
    note: "Cheating and dishonestly inducing delivery of property",
    chapter: "Chapter XI · Offences against property",
    status: "Active",
    counterpart: "ipc-420",
    parts: [
      {
        kind: "section",
        text: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is a document of title to property shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
      },
    ],
  },
  {
    id: "ipc-420",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "420",
    note: "Cheating and dishonestly inducing delivery of property",
    chapter: "Chapter XII · Offences affecting the human body",
    status: "Repealed",
    counterpart: "bns-316",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is a document of title to property, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
      },
    ],
  },
  {
    id: "bns-152",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "152",
    note: "Acts endangering sovereignty, unity and integrity of India",
    chapter: "Chapter VI · Offences against the State",
    status: "Active",
    counterpart: "ipc-124a",
    parts: [
      {
        kind: "section",
        text: "Whoever, knowingly and intentionally, excites or attempts to excite feelings of enmity or hatred towards, or disaffection towards, the Government established by law in India shall be punished with imprisonment for life, or with imprisonment which may extend to seven years, and shall also be liable to fine.",
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "Comments expressing disapprobation of the actions of the Government, made without exciting or attempting to excite hatred or contempt towards that Government, do not constitute an offence under this section.",
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "The expression “Government established by law in India” includes the State Government and the Central Government.",
      },
    ],
  },
  {
    id: "ipc-124a",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "124A",
    note: "Sedition",
    chapter: "Chapter VI · Offences against the State",
    status: "Repealed",
    counterpart: "bns-152",
    flag: "replaced",
    parts: [
      {
        kind: "section",
        text: "Whoever by words, either spoken or written, or by signs, or by visible representation, or otherwise, brings or attempts to bring into hatred or contempt, or excites or attempts to excite disaffection towards, the Government established by law in India, shall be punished with imprisonment for life, to which fine may be added…",
      },
      {
        kind: "explanation",
        label: "Explanation 1",
        text: "The expression “disaffection” includes disloyalty and all feelings of enmity.",
      },
      {
        kind: "explanation",
        label: "Explanation 2",
        text: "Comments expressing disapprobation of the measures of the Government, without exciting or attempting to excite hatred, contempt or disaffection, do not constitute an offence.",
      },
    ],
  },
  {
    id: "bnss-528",
    code: "BNSS",
    act: "Bharatiya Nagarik Suraksha Sanhita, 2023",
    year: 2023,
    section: "528",
    note: "Savings of inherent powers of High Court",
    chapter: "Chapter XXXVII · Miscellaneous",
    status: "Active",
    counterpart: "crcp-482",
    parts: [
      {
        kind: "section",
        text: "Nothing in this Sanhita shall be deemed to limit or affect the inherent powers of the High Court to make such orders as may be necessary to give effect to any order under this Sanhita, or to prevent abuse of the process of any Court or otherwise to secure the ends of justice.",
      },
    ],
  },
  {
    id: "crcp-482",
    code: "CrPC",
    act: "Code of Criminal Procedure, 1973",
    year: 1973,
    section: "482",
    note: "Saving of inherent powers of High Court",
    chapter: "Chapter XLVI · Miscellaneous",
    status: "Repealed",
    counterpart: "bnss-528",
    flag: "retained",
    parts: [
      {
        kind: "section",
        text: "Nothing in this Code shall be deemed to limit or affect the inherent powers of the High Court to make such orders as may be necessary to give effect to any order under this Code, or to prevent abuse of the process of any Court or otherwise to secure the ends of justice.",
      },
    ],
  },
  {
    id: "bnss-144",
    code: "BNSS",
    act: "Bharatiya Nagarik Suraksha Sanhita, 2023",
    year: 2023,
    section: "144",
    note: "Maintenance of wife, children and parents",
    chapter: "Chapter XII · Maintenance",
    status: "Active",
    counterpart: "crcp-125",
    parts: [
      {
        kind: "section",
        text: "If any person having sufficient means neglects or refuses to maintain— (a) his wife, except a wife who is proved to have committed adultery; (b) his child, whether born within or outside marriage… (c) his father or mother,— then the Magistrate of the first class may, on a petition in that behalf, order him to make a monthly allowance for maintenance…",
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "No father or mother who is unable to maintain himself or herself shall have claim for maintenance if he or she is able to maintain himself or herself from his or her own property, or from his or her children.",
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "For the purposes of this section, “child” includes a son who has not attained the age of eighteen years and a daughter who has not been married and who is unable to maintain herself.",
      },
    ],
  },
  {
    id: "crcp-125",
    code: "CrPC",
    act: "Code of Criminal Procedure, 1973",
    year: 1973,
    section: "125",
    note: "Maintenance of wife, children and parents",
    chapter: "Chapter IX · Maintenance",
    status: "Repealed",
    counterpart: "bnss-144",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "If any person having sufficient means neglects or refuses to maintain— (a) his wife, unable to maintain herself; (b) his legitimate or illegitimate minor child, whether married or not, unable to maintain itself; (c) his legitimate or illegitimate child (not being a married daughter) who has attained a majority… then such Magistrate may order such person to make a monthly allowance for maintenance…",
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "No wife shall be entitled to receive an allowance from her husband if she is living separately from him of her own accord without any sufficient reason or if she is living in adultery.",
      },
    ],
  },
  {
    id: "bsa-49",
    code: "BSA",
    act: "Bharatiya Sakshya Adhiniyam, 2023",
    year: 2023,
    section: "49",
    note: "Proof of previous good character in criminal proceedings",
    chapter: "Chapter VI · Of the proof of facts",
    status: "Active",
    counterpart: "iea-53",
    parts: [
      {
        kind: "section",
        text: "In criminal proceedings the fact that the accused is a person of previous good character shall be deemed to be relevant.",
      },
    ],
  },
  {
    id: "iea-53",
    code: "IEA",
    act: "Indian Evidence Act, 1872",
    year: 1872,
    section: "53",
    note: "Character affecting damages or punishment",
    chapter: "Chapter IX · Of such facts as relate to admission and communication",
    status: "Repealed",
    counterpart: "bsa-49",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "In suits for damages, the fact that the defendant was, or was not, a person of good character, is relevant. In criminal proceedings, the fact that the accused was a person of good character is relevant.",
      },
    ],
  },
  {
    id: "ndps-37",
    code: "NDPS",
    act: "Narcotic Drugs and Psychotropic Substances Act, 1985",
    year: 1985,
    section: "37",
    note: "Offences for which trial to be in special court — bail conditions",
    chapter: "Chapter IV · Offences and penalties",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "Notwithstanding anything in the Code of Criminal Procedure, 1973, no person accused of an offence punishable under Section 19 or Section 24 or Section 27-A, or for a contravention in relation to commercial quantitiy of narcotic drugs shall be released on bail…",
      },
      {
        kind: "clause",
        label: "(i)",
        text: "there are reasonable grounds for believing that he is not guilty of such offence; and",
      },
      {
        kind: "clause",
        label: "(ii)",
        text: "he is not likely to commit any offence while on bail.",
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "The Court shall, while granting bail, take into account the great importance of the public interest and shall have regard to the nature and gravity of the offence.",
      },
    ],
  },
  {
    id: "cpc-9",
    code: "CPC",
    act: "Code of Civil Procedure, 1908",
    year: 1908,
    section: "9",
    note: "Courts to try all suits of a civil nature",
    chapter: "Part I · Jurisdiction of the Civil Courts",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "The Courts shall (subject to the provisions contained in this Code or of any other law for the time being in force) have cognizance of all suits of a civil nature excepting suits of which their cognizance is either expressly or by implication barred.",
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A suit for a decree for a right to worship at a temple is a suit of a civil nature.",
      },
      {
        kind: "illustration",
        label: "Illustration (b)",
        text: "A suit in which the right to property or to an office is contested is a suit of a civil nature.",
      },
    ],
  },
  {
    id: "ica-10",
    code: "ICA",
    act: "Indian Contract Act, 1872",
    year: 1872,
    section: "10",
    note: "What agreements are contracts",
    chapter: "Chapter I · Of the communication, acceptance and revocation of proposals",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not hereby expressly declared to be void.",
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "Nothing herein contained shall affect any law in force in India and not hereby expressly repealed by which any contract required to be made in writing or otherwise in the manner prescribed by that law.",
      },
      {
        kind: "explanation",
        label: "Explanation 1",
        text: "Nothing herein contained shall affect the law in force at the present moment regarding contracts made by parties who are not competent to contract.",
      },
    ],
  },
  {
    id: "const-21",
    code: "Constitution",
    act: "Constitution of India",
    year: 1950,
    section: "Article 21",
    note: "Protection of life and personal liberty",
    chapter: "Part III · Fundamental Rights",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
      },
    ],
  },
];

export const byId = (id: string) => CORPUS.find((s) => s.id === id);

export interface Mapping {
  from: string;
  to: string;
  relation: "Renumbered" | "Split" | "Replaced" | "Retained verbatim";
  delta: string;
  risk: "low" | "medium" | "high";
}

export const MAPPINGS: Mapping[] = [
  {
    from: "ipc-302",
    to: "bns-103",
    relation: "Renumbered",
    delta: "Sentence carried over unchanged. Charge-frames, bail orders and precedents citing s.302 resolve to s.103 for post-commencement offences.",
    risk: "low",
  },
  {
    from: "ipc-300",
    to: "bns-102",
    relation: "Retained verbatim",
    delta: "All five exceptions and the illustration block remain inside the section boundary. A window chunker severs Exception 2 from the operative clause 11 times in this section.",
    risk: "low",
  },
  {
    from: "ipc-304",
    to: "bns-104",
    relation: "Split",
    delta: "One section, two limbs → two sections. The mental requirement decides which provision is charged; retrieval must not treat s.304 as one-to-one.",
    risk: "high",
  },
  {
    from: "ipc-420",
    to: "bns-316",
    relation: "Renumbered",
    delta: "Text and sentence unchanged. Compoundability now tracks the Sanhita’s schedule, not the Code’s.",
    risk: "medium",
  },
  {
    from: "ipc-124a",
    to: "bns-152",
    relation: "Replaced",
    delta: "Sedition is not reproduced as a standalone offence. Elements are restated with a protective proviso for disapprobation — do not map one-to-one.",
    risk: "high",
  },
  {
    from: "crcp-482",
    to: "bnss-528",
    relation: "Retained verbatim",
    delta: "Two substitutions only: “this Code” → “this Sanhita”. Inherent powers are otherwise word-for-word.",
    risk: "low",
  },
  {
    from: "crcp-125",
    to: "bnss-144",
    relation: "Renumbered",
    delta: "Maintenance claim by a parent is now on the face of the section. Proviso realigned; verify against the Gazette text before pleading.",
    risk: "medium",
  },
  {
    from: "iea-53",
    to: "bsa-49",
    relation: "Renumbered",
    delta: "The civil limb on damages is no longer restated inside the section. Retrieval returns BSA s.49 with the IEA s.53 context note attached.",
    risk: "medium",
  },
];

/** The single boundary grammar. Every chunk in the index is produced by it. */
export const GRAMMAR: { group: string; pattern: string; role: string; highlights: AnchorKind[] }[] = [
  {
    group: "open",
    pattern: String.raw`(?:^|\r?\n)[ \t]{0,8}`,
    role: "A unit may begin only at the start of a line. Running heads, chapter rules and page furniture are stripped before this runs, so nothing but a printed section number can open a chunk.",
    highlights: [],
  },
  {
    group: "number",
    pattern: String.raw`(?<number>\d{1,4}[A-Za-z]?|[Aa]rticle\s+\d+[A-Z]*)`,
    role: "103, 124A, 304B, Article 21. The letter suffix is precisely where slicing by length fails — 124A is not 124, and 304A is not 304.",
    highlights: ["section"],
  },
  {
    group: "marginal",
    pattern: String.raw`\.[ \t]*(?<marginal>[^\n]{2,140}?\.[ \t]*—)`,
    role: "The marginal note is bound to its number by the em-dash the drafter printed. It travels with the unit and is never indexed as a paragraph of its own.",
    highlights: ["section"],
  },
  {
    group: "clause",
    pattern: `(?<clause>\\n\\s*(?:\\([a-z0-9ivx]+\\)|first|secondly|thirdly|fourthly)[,.)]?\\s)`,
    role: "Keeps (a), (b), (i), (ii) and the ordinal drafting style attached to the operative sentence that governs them.",
    highlights: ["clause"],
  },
  {
    group: "proviso",
    pattern: `(?<proviso>\\n\\s*(?:Provided\\s+that|Provided\\s+further\\s+that)[\\s\\S]*?(?=\\n\\s*(?:Provided|Explanation|Illustration|SECTION)|\\Z))`,
    role: "A proviso that leaves the section is a different case. Anchored, always.",
    highlights: ["proviso"],
  },
  {
    group: "exception",
    pattern: `(?<exception>\\n\\s*Exception\\s*\\d*[\\s\\S]*?(?=\\n\\s*(?:Exception|Illustration|SECTION\\s+\\d)|\\Z))`,
    role: "Exceptions are pulled into the parent unit so that “not murder” cannot be retrieved without “murder”.",
    highlights: ["exception"],
  },
  {
    group: "explanation",
    pattern: `(?<explanation>\\n\\s*Explanation\\s*\\d*[\\s\\S]*?(?=\\n\\s*(?:Explanation|Illustration|SECTION\\s+\\d)|\\Z))`,
    role: "Deeming provisions and definitional explanations stay with the section they explain.",
    highlights: ["explanation"],
  },
  {
    group: "illustration",
    pattern: `(?<illustration>\\n\\s*Illustration[s]?[\\s\\S]*?(?=\\n\\s*(?:SECTION\\s+\\d)|\\Z))`,
    role: "Retained so that the worked example is cited with the same authority as the rule.",
    highlights: ["illustration"],
  },
  {
    group: "stop",
    pattern: String.raw`(?=(?:\r?\n)[ \t]{0,8}(?:\d{1,4}[A-Za-z]?\.|[Aa]rticle\s+\d+[A-Z]*\.)|\r?\n*[ \t]*$)`,
    role: "The look-ahead that closes the unit: the next printed section number, or the end of the statute. Chunk length is a consequence of drafting, never a parameter.",
    highlights: [],
  },
];

export const ANCHOR_LABELS: { kind: AnchorKind; label: string; note: string }[] = [
  { kind: "section", label: "SECTION + number + marginal note", note: "unit opener" },
  { kind: "clause", label: "clause / sub-clause ordinals", note: "(a) (b) · first, secondly" },
  { kind: "proviso", label: "Provided that", note: "condition on the rule" },
  { kind: "exception", label: "Exception n", note: "carving out of liability" },
  { kind: "explanation", label: "Explanation n", note: "deeming & definition" },
  { kind: "illustration", label: "Illustrations", note: "worked examples" },
];

export const SHORT_CODE_COLLISIONS = [
  "CA — Competition Act, 2002 · Copyright Act, 1957",
  "ITA — Indian Trusts Act, 1882 · Information Technology Act, 2000",
  "FA — Factories Act, 1948 · Forest Act, 1927",
];

export const PIPELINE = [
  {
    n: "01",
    title: "Bare-act ingest",
    body: "Legislative Department text, amendment Acts and Gazette corrections merged into one canonical string per statute. No commentary, no digests, no headnote language enters the index.",
    meta: "38 statutes",
  },
  {
    n: "02",
    title: "Boundary grammar",
    body: "One deterministic regular expression per statute walks the text and closes a unit only at the next section anchor. Chunk length is a consequence of drafting, never a parameter.",
    meta: "9 capture groups",
  },
  {
    n: "03",
    title: "Hierarchical tree",
    body: "Each unit is filed under Act → Chapter → Part → Section → Clause, so a query can be answered at the exact level of granularity a pleading cites, and rolled up when a court needs the parent.",
    meta: "5 levels",
  },
  {
    n: "04",
    title: "Correspondence map",
    body: "Repealed and re-enacted provisions are linked by relation type — renumbered, split, replaced, retained verbatim — with the relation shown to the user instead of hidden behind a similarity score.",
    meta: "IPC→BNS · CrPC→BNSS · IEA→BSA",
  },
  {
    n: "05",
    title: "Retrieval & assembly",
    body: "Candidates are scored on statutory identity first, then textually. The retrieved unit is emitted whole, with its provisos and exceptions, and cut only at paragraph boundaries inside the unit.",
    meta: "no windowing",
  },
  {
    n: "06",
    title: "Citation ledger",
    body: "Every sentence returned carries the act, section, clause and the character offset of the source line. An assertion without a resolvable offset does not leave the pipeline.",
    meta: "offset-level",
  },
];

export const FAQ = [
  {
    q: "Why not fixed-size chunking with overlap?",
    a: "Because overlap repairs recall and destroys the unit. A 512-token window with 64-token overlap severs the proviso from the rule it qualifies, and the model then reads a condition as if it were the whole of the law. The grammar in step 02 uses the drafter’s own boundaries, so a section can be long — that is the correct length.",
  },
  {
    q: "What happens to sections that run to sixty pages?",
    a: "They are indexed as one logical unit and addressed by a clause-level path. Retrieval returns the whole unit to the citation resolver and windows only the display, so nothing is quoted without the parent provision attached.",
  },
  {
    q: "Do you index judgments?",
    a: "Not inside the statutory index. Reports are a separate corpus with a separate grammar, because a paragraph of a judgment is not a provision of law and must never be returned as though it were.",
  },
  {
    q: "How are the 2023 criminal laws handled against the repealed Codes?",
    a: "Both are indexed, both are addressable, and the status is carried on every unit. For an offence alleged before 01.07.2024 the resolver pins IPC, CrPC and IEA; after it, BNS, BNSS and BSA — and the correspondence relation is printed next to the answer.",
  },
  {
    q: "What does a batch of 50 actually do?",
    a: "Fifty independent queries are compiled into one queue, de-duplicated on statutory identity, and resolved concurrently with per-query status. You get a table: query, resolved citation, unit id, anchor count, and time. Results export as CSV or a citation annexure.",
  },
  {
    q: "Can it be trusted over a lawyer’s reading?",
    a: "No. It is an index with a grammar and a ledger. Every answer is a pointer to text you can open and read; the judgement on that text stays with you.",
  },
];

export const ACCESS = [
  {
    tier: "Chambers",
    price: "₹ 2,400",
    per: "per month · 1 user",
    lines: [
      "Full 38-act statutory index",
      "Section comparison, 2-pane",
      "Batch runs — 10 queries",
      "Citation strings, copy-ready",
    ],
  },
  {
    tier: "Bench & Registry",
    price: "₹ 9,800",
    per: "per month · up to 10 users",
    lines: [
      "Everything in Chambers",
      "Batch runs — 50 queries",
      "CSV and annexure export",
      "Offset ledger on every answer",
      "Older, unrepealed texts on request",
    ],
    featured: true,
  },
  {
    tier: "Firm / Litigation desk",
    price: "On request",
    per: "named counsel, unlimited queue",
    lines: [
      "Private corpus overlay",
      "API with the same grammar",
      "Report corpus as a second index",
      "Deployment in your VPC",
    ],
  },
];
