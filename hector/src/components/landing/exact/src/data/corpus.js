const CORPUS = [
  {
    id: "bns-103",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "103",
    note: "Punishment for murder",
    chapter: "Chapter VI \xB7 Offences affecting the human body",
    status: "Active",
    counterpart: "ipc-302",
    parts: [
      {
        kind: "section",
        label: "SECTION 103",
        text: "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."
      }
    ]
  },
  {
    id: "ipc-302",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "302",
    note: "Punishment for murder",
    chapter: "Chapter XVI \xB7 Offences affecting the human body",
    status: "Repealed",
    counterpart: "bns-103",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        label: "SECTION 302",
        text: "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."
      }
    ]
  },
  {
    id: "bns-101",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "101",
    note: "Murder",
    chapter: "Chapter VI \xB7 Offences affecting the human body",
    status: "Active",
    counterpart: "ipc-300",
    parts: [
      {
        kind: "section",
        text: "Except in the cases hereinafter excepted, culpable homicide is murder,\u2014"
      },
      {
        kind: "clause",
        label: "(a)",
        text: "if the act by which the death is caused is done with the intention of causing death; or"
      },
      {
        kind: "clause",
        label: "(b)",
        text: "if the act by which the death is caused is done with the intention of causing such bodily injury as the offender knows to be likely to cause the death of the person to whom the harm is caused; or"
      },
      {
        kind: "clause",
        label: "(c)",
        text: "if the act by which the death is caused is done with the intention of causing bodily injury to any person and the bodily injury intended to be inflicted is sufficient in the ordinary course of nature to cause death; or"
      },
      {
        kind: "clause",
        label: "(d)",
        text: "if the person committing the act by which the death is caused, knows that it is so imminently dangerous that it must, in all probability, cause death, or such bodily injury as is likely to cause death, and commits such act without any excuse for incurring the risk of causing death or such injury as aforesaid."
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A shoots Z with the intention of killing him. Z dies in consequence. A commits murder."
      },
      {
        kind: "exception",
        label: "Exception 1",
        text: "Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation or causes the death of any other person by mistake or accident:"
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "Provided that the provocation is not,\u2014 (a) sought or voluntarily provoked by the offender as an excuse for killing or doing harm to any person; (b) given by anything done in obedience to the law, or by a public servant in the lawful exercise of the powers of such public servant; (c) given by anything done in the lawful exercise of the right of private defence."
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "Whether the provocation was grave and sudden enough to prevent the offence from amounting to murder is a question of fact."
      },
      {
        kind: "exception",
        label: "Exception 2",
        text: "Culpable homicide is not murder if the offender in the exercise in good faith of the right of private defence of person or property, exceeds the power given to him by law and causes the death of the person against whom he is exercising such right of defence without premeditation\u2026"
      },
      {
        kind: "exception",
        label: "Exception 3",
        text: "Culpable homicide is not murder if the offender, being a public servant or aiding a public servant acting for the advancement of public justice, exceeds the powers given to him by law, and causes death by doing an act which he, in good faith, believes to be lawful\u2026"
      },
      {
        kind: "exception",
        label: "Exception 4",
        text: "Culpable homicide is not murder if it is committed without premeditation in a sudden fight in the heat of passion upon a sudden quarrel and without the offender's having taken undue advantage or acted in a cruel or unusual manner."
      },
      {
        kind: "exception",
        label: "Exception 5",
        text: "Culpable homicide is not murder when the person whose death is caused, being above the age of eighteen years, suffers death or takes the risk of death with his own consent."
      }
    ]
  },
  {
    id: "ipc-300",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "300",
    note: "Murder",
    chapter: "Chapter XVI \xB7 Offences affecting the human body",
    status: "Repealed",
    counterpart: "bns-101",
    flag: "retained",
    parts: [
      {
        kind: "section",
        text: "Except in the cases hereinafter excepted, culpable homicide is murder,\u2014"
      },
      {
        kind: "clause",
        label: "first",
        text: "if the act by which the death is caused is done with the intention of causing death;"
      },
      {
        kind: "clause",
        label: "secondly",
        text: "if it is done with the intention of causing such bodily injury as the offender knows to be likely to cause death;"
      },
      {
        kind: "clause",
        label: "thirdly",
        text: "if it is done with the intention of causing bodily injury which the offender knows to be sufficient in the ordinary course of nature to cause death;"
      },
      {
        kind: "clause",
        label: "fourthly",
        text: "if the offender does the act known to be so imminently dangerous that it must in all probability cause death\u2026"
      },
      {
        kind: "exception",
        label: "Exception 1",
        text: "Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation\u2026"
      },
      {
        kind: "exception",
        label: "Exception 2",
        text: "Culpable homicide is not murder if the offender, in the exercise in good faith of private defence of person or property, exceeds the power given to him\u2026"
      },
      {
        kind: "exception",
        label: "Exception 3",
        text: "Culpable homicide is not murder if a public servant, acting in the discharge of his duty, exceeds the powers of a public servant\u2026"
      },
      {
        kind: "exception",
        label: "Exception 4",
        text: "Culpable homicide is not murder if the offender, whilst in sudden fight, causes death in the heat of passion without premeditation\u2026"
      },
      {
        kind: "exception",
        label: "Exception 5",
        text: "Culpable homicide is not murder if the person whose death is caused, being above the age of eighteen years, suffers death at the hands of the victim with his own consent\u2026"
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A, on sudden provocation received from B, kills B in the heat of passion. A has committed culpable homicide not amounting to murder."
      }
    ]
  },
  {
    id: "bns-105",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "105",
    note: "Punishment for culpable homicide not amounting to murder",
    chapter: "Chapter VI \xB7 Offences affecting the human body",
    status: "Active",
    counterpart: "ipc-304",
    parts: [
      {
        kind: "section",
        text: "Whoever commits culpable homicide not amounting to murder, shall be punished with imprisonment for life, or imprisonment of either description for a term which shall not be less than five years but which may extend to ten years, and shall also be liable to fine, if the act by which the death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death; or with imprisonment of either description for a term which may extend to ten years and with fine, if the act is done with the knowledge that it is likely to cause death, but without any intention to cause death, or to cause such bodily injury as is likely to cause death."
      }
    ]
  },
  {
    id: "ipc-304",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "304",
    note: "Punishment for culpable homicide not amounting to murder",
    chapter: "Chapter XVI \xB7 Offences affecting the human body",
    status: "Repealed",
    counterpart: "bns-105",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine, if the act by which the death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death,"
      },
      {
        kind: "clause",
        label: "second part",
        text: "and with imprisonment of either description for a term which may extend to ten years, or with fine, or with both, if the act is done with the knowledge that it is likely to cause death, but without any intention to cause death\u2026"
      }
    ]
  },
  {
    id: "bns-318",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "318",
    note: "Cheating",
    chapter: "Chapter XVII \xB7 Offences against property",
    status: "Active",
    counterpart: "ipc-420",
    parts: [
      {
        kind: "section",
        text: "(1) Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property, is said to cheat."
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "A dishonest concealment of facts is a deception within the meaning of this section."
      },
      {
        kind: "clause",
        label: "(2)",
        text: "Whoever cheats shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both."
      },
      {
        kind: "clause",
        label: "(3)",
        text: "Whoever cheats with the knowledge that he is likely thereby to cause wrongful loss to a person whose interest in the transaction to which the cheating relates, he was bound, either by law, or by a legal contract, to protect, shall be punished with imprisonment of either description for a term which may extend to five years, or with fine, or with both."
      },
      {
        kind: "clause",
        label: "(4)",
        text: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."
      }
    ]
  },
  {
    id: "ipc-420",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "420",
    note: "Cheating and dishonestly inducing delivery of property",
    chapter: "Chapter XVII \xB7 Offences against property",
    status: "Repealed",
    counterpart: "bns-318",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."
      }
    ]
  },
  {
    id: "bns-152",
    code: "BNS",
    act: "Bharatiya Nyaya Sanhita, 2023",
    year: 2023,
    section: "152",
    note: "Acts endangering sovereignty, unity and integrity of India",
    chapter: "Chapter VI \xB7 Offences against the State",
    status: "Active",
    counterpart: "ipc-124a",
    parts: [
      {
        kind: "section",
        text: "Whoever, knowingly and intentionally, excites or attempts to excite feelings of enmity or hatred towards, or disaffection towards, the Government established by law in India shall be punished with imprisonment for life, or with imprisonment which may extend to seven years, and shall also be liable to fine."
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "Comments expressing disapprobation of the actions of the Government, made without exciting or attempting to excite hatred or contempt towards that Government, do not constitute an offence under this section."
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "The expression \u201CGovernment established by law in India\u201D includes the State Government and the Central Government."
      }
    ]
  },
  {
    id: "ipc-124a",
    code: "IPC",
    act: "Indian Penal Code, 1860",
    year: 1860,
    section: "124A",
    note: "Sedition",
    chapter: "Chapter VI \xB7 Offences against the State",
    status: "Repealed",
    counterpart: "bns-152",
    flag: "replaced",
    parts: [
      {
        kind: "section",
        text: "Whoever by words, either spoken or written, or by signs, or by visible representation, or otherwise, brings or attempts to bring into hatred or contempt, or excites or attempts to excite disaffection towards, the Government established by law in India, shall be punished with imprisonment for life, to which fine may be added\u2026"
      },
      {
        kind: "explanation",
        label: "Explanation 1",
        text: "The expression \u201Cdisaffection\u201D includes disloyalty and all feelings of enmity."
      },
      {
        kind: "explanation",
        label: "Explanation 2",
        text: "Comments expressing disapprobation of the measures of the Government, without exciting or attempting to excite hatred, contempt or disaffection, do not constitute an offence."
      }
    ]
  },
  {
    id: "bnss-528",
    code: "BNSS",
    act: "Bharatiya Nagarik Suraksha Sanhita, 2023",
    year: 2023,
    section: "528",
    note: "Savings of inherent powers of High Court",
    chapter: "Chapter XXXVII \xB7 Miscellaneous",
    status: "Active",
    counterpart: "crcp-482",
    parts: [
      {
        kind: "section",
        text: "Nothing in this Sanhita shall be deemed to limit or affect the inherent powers of the High Court to make such orders as may be necessary to give effect to any order under this Sanhita, or to prevent abuse of the process of any Court or otherwise to secure the ends of justice."
      }
    ]
  },
  {
    id: "crcp-482",
    code: "CrPC",
    act: "Code of Criminal Procedure, 1973",
    year: 1973,
    section: "482",
    note: "Saving of inherent powers of High Court",
    chapter: "Chapter XLVI \xB7 Miscellaneous",
    status: "Repealed",
    counterpart: "bnss-528",
    flag: "retained",
    parts: [
      {
        kind: "section",
        text: "Nothing in this Code shall be deemed to limit or affect the inherent powers of the High Court to make such orders as may be necessary to give effect to any order under this Code, or to prevent abuse of the process of any Court or otherwise to secure the ends of justice."
      }
    ]
  },
  {
    id: "bnss-144",
    code: "BNSS",
    act: "Bharatiya Nagarik Suraksha Sanhita, 2023",
    year: 2023,
    section: "144",
    note: "Maintenance of wife, children and parents",
    chapter: "Chapter XII \xB7 Maintenance",
    status: "Active",
    counterpart: "crcp-125",
    parts: [
      {
        kind: "section",
        text: "If any person having sufficient means neglects or refuses to maintain\u2014 (a) his wife, except a wife who is proved to have committed adultery; (b) his child, whether born within or outside marriage\u2026 (c) his father or mother,\u2014 then the Magistrate of the first class may, on a petition in that behalf, order him to make a monthly allowance for maintenance\u2026"
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "No father or mother who is unable to maintain himself or herself shall have claim for maintenance if he or she is able to maintain himself or herself from his or her own property, or from his or her children."
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "For the purposes of this section, \u201Cchild\u201D includes a son who has not attained the age of eighteen years and a daughter who has not been married and who is unable to maintain herself."
      }
    ]
  },
  {
    id: "crcp-125",
    code: "CrPC",
    act: "Code of Criminal Procedure, 1973",
    year: 1973,
    section: "125",
    note: "Maintenance of wife, children and parents",
    chapter: "Chapter IX \xB7 Maintenance",
    status: "Repealed",
    counterpart: "bnss-144",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "If any person having sufficient means neglects or refuses to maintain\u2014 (a) his wife, unable to maintain herself; (b) his legitimate or illegitimate minor child, whether married or not, unable to maintain itself; (c) his legitimate or illegitimate child (not being a married daughter) who has attained a majority\u2026 then such Magistrate may order such person to make a monthly allowance for maintenance\u2026"
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "No wife shall be entitled to receive an allowance from her husband if she is living separately from him of her own accord without any sufficient reason or if she is living in adultery."
      }
    ]
  },
  {
    id: "bsa-47",
    code: "BSA",
    act: "Bharatiya Sakshya Adhiniyam, 2023",
    year: 2023,
    section: "47",
    note: "In criminal cases previous good character relevant",
    chapter: "Chapter II \xB7 Relevancy of facts",
    status: "Active",
    counterpart: "iea-53",
    parts: [
      {
        kind: "section",
        text: "In criminal proceedings the fact that the person accused is of a good character, is relevant."
      }
    ]
  },
  {
    id: "iea-53",
    code: "IEA",
    act: "Indian Evidence Act, 1872",
    year: 1872,
    section: "53",
    note: "In criminal cases previous good character relevant",
    chapter: "Chapter II \xB7 Of the relevancy of facts",
    status: "Repealed",
    counterpart: "bsa-47",
    flag: "renumbered",
    parts: [
      {
        kind: "section",
        text: "In criminal proceedings, the fact that the person accused is of a good character is relevant."
      }
    ]
  },
  {
    id: "ndps-37",
    code: "NDPS",
    act: "Narcotic Drugs and Psychotropic Substances Act, 1985",
    year: 1985,
    section: "37",
    note: "Offences for which trial to be in special court \u2014 bail conditions",
    chapter: "Chapter IV \xB7 Offences and penalties",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "Notwithstanding anything in the Code of Criminal Procedure, 1973, no person accused of an offence punishable under Section 19 or Section 24 or Section 27-A, or for a contravention in relation to commercial quantitiy of narcotic drugs shall be released on bail\u2026"
      },
      {
        kind: "clause",
        label: "(i)",
        text: "there are reasonable grounds for believing that he is not guilty of such offence; and"
      },
      {
        kind: "clause",
        label: "(ii)",
        text: "he is not likely to commit any offence while on bail."
      },
      {
        kind: "explanation",
        label: "Explanation",
        text: "The Court shall, while granting bail, take into account the great importance of the public interest and shall have regard to the nature and gravity of the offence."
      }
    ]
  },
  {
    id: "cpc-9",
    code: "CPC",
    act: "Code of Civil Procedure, 1908",
    year: 1908,
    section: "9",
    note: "Courts to try all suits of a civil nature",
    chapter: "Part I \xB7 Jurisdiction of the Civil Courts",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "The Courts shall (subject to the provisions contained in this Code or of any other law for the time being in force) have cognizance of all suits of a civil nature excepting suits of which their cognizance is either expressly or by implication barred."
      },
      {
        kind: "illustration",
        label: "Illustration (a)",
        text: "A suit for a decree for a right to worship at a temple is a suit of a civil nature."
      },
      {
        kind: "illustration",
        label: "Illustration (b)",
        text: "A suit in which the right to property or to an office is contested is a suit of a civil nature."
      }
    ]
  },
  {
    id: "ica-10",
    code: "ICA",
    act: "Indian Contract Act, 1872",
    year: 1872,
    section: "10",
    note: "What agreements are contracts",
    chapter: "Chapter I \xB7 Of the communication, acceptance and revocation of proposals",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not hereby expressly declared to be void."
      },
      {
        kind: "proviso",
        label: "Proviso",
        text: "Nothing herein contained shall affect any law in force in India and not hereby expressly repealed by which any contract required to be made in writing or otherwise in the manner prescribed by that law."
      },
      {
        kind: "explanation",
        label: "Explanation 1",
        text: "Nothing herein contained shall affect the law in force at the present moment regarding contracts made by parties who are not competent to contract."
      }
    ]
  },
  {
    id: "const-21",
    code: "Constitution",
    act: "Constitution of India",
    year: 1950,
    section: "Article 21",
    note: "Protection of life and personal liberty",
    chapter: "Part III \xB7 Fundamental Rights",
    status: "Active",
    parts: [
      {
        kind: "section",
        text: "No person shall be deprived of his life or personal liberty except according to procedure established by law."
      }
    ]
  }
];
const byId = (id) => CORPUS.find((s) => s.id === id);
const MAPPINGS = [
  {
    from: "ipc-302",
    to: "bns-103",
    relation: "Renumbered",
    delta: "Sentence carried over unchanged. Charge-frames, bail orders and precedents citing s.302 resolve to s.103 for post-commencement offences.",
    risk: "low"
  },
  {
    from: "ipc-300",
    to: "bns-101",
    relation: "Retained",
    delta: "Same definition carried over; the ordinal limbs were re-lettered to (a)\u2013(d). All five exceptions and the illustration block remain inside the section boundary. A window chunker severs Exception 2 from the operative clause 11 times in this section.",
    risk: "low"
  },
  {
    from: "ipc-304",
    to: "bns-105",
    relation: "Renumbered",
    delta: "Both limbs sit in one section under the Sanhita, and limb 1 now carries a five-year floor. The mental requirement decides which provision is charged; retrieval must not treat s.304 as one-to-one.",
    risk: "medium"
  },
  {
    from: "ipc-420",
    to: "bns-318",
    relation: "Renumbered",
    delta: "The seven-year limb for inducing delivery of property is now s.318(4) \u2014 a clause-level citation, not a standalone section. Compoundability now tracks the Sanhita\u2019s schedule, not the Code\u2019s.",
    risk: "medium"
  },
  {
    from: "ipc-124a",
    to: "bns-152",
    relation: "Replaced",
    delta: "Sedition is not reproduced as a standalone offence. Elements are restated with a protective proviso for disapprobation \u2014 do not map one-to-one.",
    risk: "high"
  },
  {
    from: "crcp-482",
    to: "bnss-528",
    relation: "Retained verbatim",
    delta: "Two substitutions only: \u201Cthis Code\u201D \u2192 \u201Cthis Sanhita\u201D. Inherent powers are otherwise word-for-word.",
    risk: "low"
  },
  {
    from: "crcp-125",
    to: "bnss-144",
    relation: "Renumbered",
    delta: "Maintenance claim by a parent is now on the face of the section. Proviso realigned; verify against the Gazette text before pleading.",
    risk: "medium"
  },
  {
    from: "iea-53",
    to: "bsa-47",
    relation: "Renumbered",
    delta: "Word-for-word the same sentence in both enactments. The civil limb on damages is no longer restated inside the section. Retrieval returns BSA s.47 with the IEA s.53 context note attached.",
    risk: "low"
  }
];
const GRAMMAR = [
  {
    group: "open",
    pattern: String.raw`(?:^|\n)`,
    role: "A unit may begin only at the start of a line. Running heads, chapter rules and page furniture are stripped before this runs, so nothing but a printed section number can open a chunk.",
    highlights: []
  },
  {
    group: "number",
    pattern: String.raw`(?:(?:[Ss]ection|[Ss]ec\.?|s\.)\s*(\d{1,4}[A-Z]?)\.?\s+|(\d{1,4}[A-Z]?)\.\s+[^a-z\d])`,
    role: "Section 103, Sec. 124A, s. 304B \u2014 or a printed 103. at line start. The letter suffix is precisely where slicing by length fails: 124A is not 124, and 304A is not 304.",
    highlights: ["section"]
  },
  {
    group: "marginal",
    pattern: String.raw`\.\s*[-\u2013\u2014]|--|[\u2013\u2014]`,
    role: "The marginal note is cut from the first line at the dash the drafter printed \u2014 .\u2014, \u2014 or \u2013. It travels with the unit and is never indexed as a paragraph of its own.",
    highlights: ["section"]
  },
  {
    group: "clause",
    pattern: String.raw`\(([a-zA-Z0-9]+)\)\s+`,
    role: "Keeps (a), (b), (i), (ii) and (1), (2) attached to the operative sentence that governs them \u2014 a sub-clause is a citation target, not a paragraph of its own.",
    highlights: ["clause"]
  },
  {
    group: "proviso",
    pattern: String.raw`Provided\s+(?:that|also|further|nevertheless)`,
    role: "One rule, four printed openers: Provided that, Provided also, Provided further, Provided nevertheless. A proviso that leaves the section is a different case. Anchored, always.",
    highlights: ["proviso"]
  },
  {
    group: "exception",
    pattern: String.raw`^[ \t]*Exception`,
    role: "Exceptions are pulled into the parent unit so that \u201Cnot murder\u201D cannot be retrieved without \u201Cmurder\u201D.",
    highlights: ["exception"]
  },
  {
    group: "explanation",
    pattern: String.raw`^[ \t]*Explanation`,
    role: "Deeming provisions and definitional explanations stay with the section they explain.",
    highlights: ["explanation"]
  },
  {
    group: "illustration",
    pattern: String.raw`^[ \t]*Illustration`,
    role: "The acts print it as Illustration.\u2014, not Illustration: \u2014 so the anchor is the word itself, and the worked example is cited with the same authority as the rule.",
    highlights: ["illustration"]
  }
];
const ANCHOR_LABELS = [
  { kind: "section", label: "SECTION + number + marginal note", note: "unit opener" },
  { kind: "clause", label: "clause / sub-clause ordinals", note: "(a) (b) \xB7 first, secondly" },
  { kind: "proviso", label: "Provided that", note: "condition on the rule" },
  { kind: "exception", label: "Exception n", note: "carving out of liability" },
  { kind: "explanation", label: "Explanation n", note: "deeming & definition" },
  { kind: "illustration", label: "Illustrations", note: "worked examples" }
];
const SHORT_CODE_COLLISIONS = [
  "CA \u2014 Competition Act, 2002 \xB7 Copyright Act, 1957",
  "ITA \u2014 Indian Trusts Act, 1882 \xB7 Information Technology Act, 2000",
  "FA \u2014 Factories Act, 1948 \xB7 Forest Act, 1927"
];
const PIPELINE = [
  {
    n: "01",
    title: "Bare-act ingest",
    body: "Legislative Department text, amendment Acts and Gazette corrections merged into one canonical string per statute. No commentary, no digests, no headnote language enters the index.",
    meta: "16 statutes indexed"
  },
  {
    n: "02",
    title: "Boundary grammar",
    body: "One deterministic regular expression per statute walks the text and closes a unit only at the next section anchor. Chunk length is a consequence of drafting, never a parameter.",
    meta: "8 real patterns"
  },
  {
    n: "03",
    title: "Hierarchical tree",
    body: "Each unit is filed under Act \u2192 Chapter \u2192 Part \u2192 Section \u2192 Clause, so a query can be answered at the exact level of granularity a pleading cites, and rolled up when a court needs the parent.",
    meta: "5 levels"
  },
  {
    n: "04",
    title: "Correspondence map",
    body: "Repealed and re-enacted provisions are linked by relation type \u2014 renumbered, split, replaced, retained verbatim \u2014 with the relation shown to the user instead of hidden behind a similarity score.",
    meta: "IPC\u2192BNS \xB7 CrPC\u2192BNSS \xB7 IEA\u2192BSA"
  },
  {
    n: "05",
    title: "Retrieval & assembly",
    body: "Candidates are scored on statutory identity first, then textually. The retrieved unit is emitted whole, with its provisos and exceptions, and cut only at paragraph boundaries inside the unit.",
    meta: "no windowing"
  },
  {
    n: "06",
    title: "Citation ledger",
    body: "Every sentence returned carries the act, section, clause and the character offset of the source line. An assertion without a resolvable offset does not leave the pipeline.",
    meta: "offset-level"
  }
];
const FAQ = [
  {
    q: "Why not fixed-size chunking with overlap?",
    a: "Because overlap repairs recall and destroys the unit. A 512-token window with 64-token overlap severs the proviso from the rule it qualifies, and the model then reads a condition as if it were the whole of the law. The grammar in step 02 uses the drafter\u2019s own boundaries, so a section can be long \u2014 that is the correct length."
  },
  {
    q: "What happens to sections that run to sixty pages?",
    a: "They are indexed as one logical unit and addressed by a clause-level path. Retrieval returns the whole unit to the citation resolver and windows only the display, so nothing is quoted without the parent provision attached."
  },
  {
    q: "Do you index judgments?",
    a: "Not inside the statutory index. Reports are a separate corpus with a separate grammar, because a paragraph of a judgment is not a provision of law and must never be returned as though it were."
  },
  {
    q: "How are the 2023 criminal laws handled against the repealed Codes?",
    a: "Both are indexed, both are addressable, and the status is carried on every unit. For an offence alleged before 01.07.2024 the resolver pins IPC, CrPC and IEA; after it, BNS, BNSS and BSA \u2014 and the correspondence relation is printed next to the answer."
  },
  {
    q: "What does a batch of 50 actually do?",
    a: "Fifty independent queries are compiled into one queue, de-duplicated on statutory identity, and resolved concurrently with per-query status. You get a table: query, resolved citation, unit id, anchor count, and time. Results export as CSV or a citation annexure."
  },
  {
    q: "Can it be trusted over a lawyer\u2019s reading?",
    a: "No. It is an index with a grammar and a ledger. Every answer is a pointer to text you can open and read; the judgement on that text stays with you."
  }
];
export {
  ANCHOR_LABELS,
  CORPUS,
  FAQ,
  GRAMMAR,
  MAPPINGS,
  PIPELINE,
  SHORT_CODE_COLLISIONS,
  byId
};
