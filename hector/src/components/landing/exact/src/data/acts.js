const ACT_CATEGORIES = [
  {
    title: "Criminal",
    slug: "criminal",
    acts: [
      {
        name: "Bharatiya Nyaya Sanhita, 2023",
        year: 2023,
        code: "BNS",
        status: "Active",
        repeals: "Indian Penal Code, 1860",
        note: "Commenced 01.07.2024. Applies to offences committed on or after commencement."
      },
      {
        name: "Indian Penal Code, 1860",
        year: 1860,
        code: "IPC",
        status: "Repealed",
        note: "Continues to govern offences committed before 01.07.2024."
      }
    ]
  },
  {
    title: "Criminal Procedure",
    slug: "criminal-procedure",
    acts: [
      {
        name: "Bharatiya Nagarik Suraksha Sanhita, 2023",
        year: 2023,
        code: "BNSS",
        status: "Active",
        repeals: "Code of Criminal Procedure, 1973",
        note: "Serial numbers of cases of institution to be allocated throughout the year."
      },
      {
        name: "Code of Criminal Procedure, 1973",
        year: 1973,
        code: "CrPC",
        status: "Repealed",
        note: "Governs trials instituted before 01.07.2024."
      }
    ]
  },
  {
    title: "Evidence",
    slug: "evidence",
    acts: [
      {
        name: "Bharatiya Sakshya Adhiniyam, 2023",
        year: 2023,
        code: "BSA",
        status: "Active",
        repeals: "Indian Evidence Act, 1872",
        note: "Electronic records brought at par with documents of primary evidence."
      },
      {
        name: "Indian Evidence Act, 1872",
        year: 1872,
        code: "IEA",
        status: "Repealed",
        note: "Applies to proceedings commenced before 01.07.2024."
      }
    ]
  },
  {
    title: "Civil",
    slug: "civil",
    acts: [
      { name: "Code of Civil Procedure, 1908", year: 1908, code: "CPC", status: "Active", repeals: "Code of Civil Procedure, 1882" },
      { name: "Indian Contract Act, 1872", year: 1872, code: "ICA", status: "Active" },
      { name: "Transfer of Property Act, 1882", year: 1882, code: "TPA", status: "Active" },
      { name: "Indian Trusts Act, 1882", year: 1882, code: "ITA", status: "Active" },
      { name: "Easements Act, 1882", year: 1882, code: "EA", status: "Active" },
      { name: "Negotiable Instruments Act, 1881", year: 1881, code: "NI Act", status: "Active" },
      { name: "Limitation Act, 1963", year: 1963, code: "LA", status: "Active", repeals: "Limitation Act, 1908" },
      { name: "Specific Relief Act, 1963", year: 1963, code: "SRA", status: "Active", repeals: "Specific Relief Act, 1877" },
      { name: "Arbitration and Conciliation Act, 1996", year: 1996, code: "Arb Act", status: "Active", repeals: "Arbitration (Protocol and Convention) Act, 1937" },
      { name: "Competition Act, 2002", year: 2002, code: "CA", status: "Active", repeals: "Monopolies and Restrictive Trade Practices Act, 1969" }
    ]
  },
  {
    title: "Constitutional",
    slug: "constitutional",
    acts: [
      {
        name: "Constitution of India",
        year: 1950,
        code: "Constitution",
        status: "Active",
        note: "Parts, Articles, Clauses and Schedules indexed on separate anchors."
      }
    ]
  },
  {
    title: "Family Law",
    slug: "family",
    acts: [
      { name: "Hindu Marriage Act, 1955", year: 1955, code: "HMA", status: "Active" },
      { name: "Hindu Minority and Guardianship Act, 1956", year: 1956, code: "HMGA", status: "Active" },
      { name: "Hindu Succession Act, 1956", year: 1956, code: "HSA", status: "Active" },
      { name: "Dowry Prohibition Act, 1961", year: 1961, code: "DPA", status: "Active" },
      { name: "Family Courts Act, 1984", year: 1984, code: "FCA", status: "Active" },
      { name: "Protection of Women from Domestic Violence Act, 2005", year: 2005, code: "PWDVA", status: "Active" },
      { name: "Juvenile Justice (Care and Protection of Children) Act, 2015", year: 2015, code: "JJ Act", status: "Active", repeals: "Juvenile Justice (Care and Protection of Children) Act, 2000" }
    ]
  },
  {
    title: "Labour",
    slug: "labour",
    acts: [
      { name: "Industrial Disputes Act, 1947", year: 1947, code: "IDA", status: "Active" },
      { name: "Factories Act, 1948", year: 1948, code: "FA", status: "Active", repeals: "Factories Act, 1934" },
      { name: "Motor Vehicles Act, 1988", year: 1988, code: "MVA", status: "Active", repeals: "Motor Vehicles Act, 1939" }
    ]
  },
  {
    title: "Other",
    slug: "other",
    acts: [
      { name: "Arms Act, 1959", year: 1959, code: "AA", status: "Active", repeals: "Indian Arms Act, 1911" },
      { name: "Copyright Act, 1957", year: 1957, code: "CR", status: "Active", repeals: "Indian Copyright Act, 1914" },
      { name: "Forest Act, 1927", year: 1927, code: "FFA", status: "Active", repeals: "Indian Forest Act, 1906" },
      { name: "Narcotic Drugs and Psychotropic Substances Act, 1985", year: 1985, code: "NDPS", status: "Active" },
      { name: "Prevention of Corruption Act, 1988", year: 1988, code: "PCA", status: "Active", repeals: "Prevention of Corruption Act, 1947" },
      { name: "Environment (Protection) Act, 1986", year: 1986, code: "EPA", status: "Active" },
      { name: "Information Technology Act, 2000", year: 2e3, code: "IT Act", status: "Active" },
      { name: "Right to Information Act, 2005", year: 2005, code: "RTI", status: "Active", repeals: "Freedom of Information Act, 2002" },
      { name: "Consumer Protection Act, 2019", year: 2019, code: "CPA", status: "Active", repeals: "Consumer Protection Act, 1986" },
      { name: "Legal Services Authorities Act, 1987", year: 1987, code: "LSAA", status: "Active" },
      { name: "Gram Nyayalayas Act, 2008", year: 2008, code: "GNA", status: "Active" }
    ]
  }
];
const ALL_ACTS = ACT_CATEGORIES.flatMap((c) => c.acts);
const TOTAL_ACTS = ALL_ACTS.length;
const ACTIVE_ACTS = ALL_ACTS.filter((a) => a.status === "Active").length;
const REPEALED_ACTS = ALL_ACTS.filter((a) => a.status === "Repealed").length;
const REPEAL_LINKS = ALL_ACTS.filter((a) => a.repeals).length;
export {
  ACTIVE_ACTS,
  ACT_CATEGORIES,
  ALL_ACTS,
  REPEALED_ACTS,
  REPEAL_LINKS,
  TOTAL_ACTS
};
