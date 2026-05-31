export const sampleQueries = [
  "What is the BNS equivalent of IPC Section 302?",
  "Compare the punishment for theft under IPC and BNS",
  "What changes were made to sedition laws in BNS?",
  "Explain Section 356 BNS and its IPC counterpart",
];

export const mockResponse = {
  id: "resp-001",
  query: "What is the BNS equivalent of IPC Section 302 and how does the punishment differ?",
  answer: `**Section 302 of the Indian Penal Code (IPC)** - which deals with the **punishment for murder** - has been replaced by **Section 103 of the Bharatiya Nyaya Sanhita (BNS), 2023**.

**IPC Section 302 - Punishment for Murder:**
Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.

**BNS Section 103 - Punishment for Murder:**
Section 103(1) of the BNS retains the same punishment framework as IPC Section 302. The offender shall be punished with death, or imprisonment for life, and shall also be liable to fine.

**Key Differences & Additions under BNS:**
Section 103(2) of BNS introduces a **new sub-category** not present in IPC Section 302. It prescribes that when a group of five or more persons acting in concert commits murder on the ground of race, caste, community, sex, place of birth, language, personal belief, or any other similar ground, each member of such group shall be punished with -
- Death, or
- Imprisonment for life, and shall also be liable to fine.

**Legislative Intent:**
The addition of Section 103(2) specifically addresses mob lynching scenarios, which were previously prosecuted under a combination of IPC sections (302 r/w 149 or 34). The BNS codifies this as a standalone aggravated offence, reflecting the Supreme Court's observations in *Tehseen S. Poonawalla v. Union of India* (2018) regarding the need for specific legislation addressing mob violence.

**Transition Note:**
All pending cases registered under IPC Section 302 prior to 1st July 2024 shall continue to be tried under the IPC provisions, as per Section 1(2) of the BNS.`,
  domain: "Criminal Law",
  confidence: 97.3,
  sources: [
    {
      id: "src-001",
      bookTitle: "Ratanlal & Dhirajlal's The Indian Penal Code",
      author: "Justice K.T. Thomas & M.A. Rashid",
      chapter: "Chapter XVI - Of Offences Affecting the Human Body",
      section: "Section 302 - Punishment for Murder",
      page: 1847,
      paragraph: 3,
      relevanceScore: 0.96,
      act: "Indian Penal Code, 1860",
      matchedText: "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
      fullText: `Section 302. Punishment for murder.-Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.

COMMENT

This section provides the punishment for murder. The sentence of death is the rule and imprisonment for life is an exception. The court has to state reasons why the sentence of death is not being imposed in a case of murder. The normal rule is that the offence of murder shall be punished with the sentence of death. The court is, however, permitted in its discretion to impose the lesser penalty of imprisonment for life.

When the murder is committed in an extremely brutal, grotesque, diabolical, revolting or dastardly manner so as to arouse intense and extreme indignation of the community, the court may impose the death sentence. Where the accused does not act on any spur-of-the-moment provocation and there are no mitigating circumstances, the extreme penalty of death can be awarded.

The scope and applicability of this section has been extensively discussed by the Supreme Court in the landmark cases of Bachan Singh v. State of Punjab, (1980) 2 SCC 684 and Machhi Singh v. State of Punjab, (1983) 3 SCC 470, establishing the "rarest of rare" doctrine for imposition of the death penalty.`,
      highlightRanges: [
        { start: 0, end: 112 },
        { start: 485, end: 640 },
      ],
    },
    {
      id: "src-002",
      bookTitle: "Bharatiya Nyaya Sanhita - A Comprehensive Commentary",
      author: "Dr. R.K. Sinha",
      chapter: "Chapter VI - Of Offences Affecting the Human Body",
      section: "Section 103 - Punishment for Murder",
      page: 412,
      paragraph: 1,
      relevanceScore: 0.98,
      act: "Bharatiya Nyaya Sanhita, 2023",
      matchedText: "Section 103(2) introduces a new sub-category addressing mob lynching - when five or more persons acting in concert commit murder on specified grounds.",
      fullText: `Section 103. Punishment for murder.-

(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine.

(2) When a group of five or more persons acting in concert commits murder on the ground of race, caste or community, sex, place of birth, language, personal belief or any other similar ground each member of such group shall be punished with death or imprisonment for life, and shall also be liable to fine.

COMMENTARY

Sub-section (1) of Section 103 is a verbatim reproduction of Section 302 of the Indian Penal Code, 1860. The punishment framework remains unchanged - the court retains the discretion to impose either the death penalty or imprisonment for life.

Sub-section (2) is a significant legislative innovation with no corresponding provision in the IPC. This provision was introduced to specifically address the menace of mob lynching, which has been a growing concern in Indian society. The Supreme Court in Tehseen S. Poonawalla v. Union of India, (2018) 9 SCC 501, had expressed deep anguish over incidents of mob violence and had directed the Parliament to consider enacting a separate legislation to deal with the offence of lynching.

The inclusion of specific grounds - race, caste, community, sex, place of birth, language, and personal belief - reflects the constitutional values enshrined in Articles 14, 15, and 21 of the Constitution.`,
      highlightRanges: [
        { start: 0, end: 110 },
        { start: 113, end: 370 },
        { start: 580, end: 820 },
      ],
    },
    {
      id: "src-003",
      bookTitle: "The Code of Criminal Procedure with Bharatiya Nagarik Suraksha Sanhita",
      author: "Prof. S.N. Misra",
      chapter: "Chapter XXVI - Transitional Provisions",
      section: "Section 1(2) - Commencement and Application",
      page: 23,
      paragraph: 2,
      relevanceScore: 0.82,
      act: "Bharatiya Nyaya Sanhita, 2023",
      matchedText: "All cases registered under the erstwhile Indian Penal Code prior to the date of commencement shall continue to be governed by the provisions of the IPC.",
      fullText: `Section 1. Short title, commencement and application.-

(1) This Sanhita may be called the Bharatiya Nyaya Sanhita, 2023.

(2) It shall come into force on such date as the Central Government may, by notification in the Official Gazette, appoint, and different dates may be appointed for different provisions of this Sanhita.

COMMENTARY

The transitional provision under Section 1(2) is of critical importance to the legal fraternity. The Central Government, vide notification dated 23rd February 2024, appointed the 1st day of July, 2024 as the date on which the Bharatiya Nyaya Sanhita, 2023 came into force.

A crucial question that arises is the treatment of pending cases. It is a settled principle of criminal jurisprudence that no person shall be subjected to a penalty greater than that which might have been inflicted under the law in force at the time of the commission of the offence. This principle, embodied in Article 20(1) of the Constitution, mandates that all cases registered under the erstwhile Indian Penal Code prior to the date of commencement shall continue to be governed by the provisions of the IPC.

However, where the BNS provides for a lesser punishment for the same offence, the accused may seek the benefit of the more beneficial provision, subject to judicial interpretation.`,
      highlightRanges: [
        { start: 390, end: 580 },
      ],
    },
  ],
  pipeline: [
    {
      id: "stage-1",
      name: "Intent Routing",
      status: "completed",
      detail: "Domain classified: Criminal Law - Homicide & Bodily Offences",
    },
    {
      id: "stage-2",
      name: "Hybrid Retrieval",
      status: "completed",
      detail: "Semantic + Keyword search across 23 legal texts - 14 relevant chunks retrieved",
    },
    {
      id: "stage-3",
      name: "Hierarchical Context",
      status: "completed",
      detail: "Parent sections, chapters & act titles resolved for 3 primary sources",
    },
    {
      id: "stage-4",
      name: "Citation Grounding",
      status: "completed",
      detail: "All claims verified against source material - Confidence: 97.3%",
    },
  ],
  timestamp: "2024-12-14T10:32:45Z",
};

export const queryHistory = [
  { id: "h1", query: "IPC Section 302 to BNS mapping", timestamp: "2024-12-14T10:32:00Z", domain: "Criminal" },
  { id: "h2", query: "Sedition laws under new criminal code", timestamp: "2024-12-14T09:15:00Z", domain: "Criminal" },
  { id: "h3", query: "Bail provisions comparison IPC vs BNS", timestamp: "2024-12-13T16:45:00Z", domain: "Procedural" },
  { id: "h4", query: "Defamation under BNS Section 356", timestamp: "2024-12-13T14:20:00Z", domain: "Criminal" },
  { id: "h5", query: "Property offences transition guide", timestamp: "2024-12-12T11:30:00Z", domain: "Criminal" },
];
