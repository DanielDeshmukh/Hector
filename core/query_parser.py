"""
HECTOR Structured Query Parser
Extracts legal entities from user queries using deterministic regex patterns.
Provides fast, accurate entity extraction for structured legal queries.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LegalEntities:
    """Structured legal entities extracted from a query."""
    sections: List[str] = field(default_factory=list)
    acts: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    courts: List[str] = field(default_factory=list)
    ipc_sections: List[str] = field(default_factory=list)
    bns_sections: List[str] = field(default_factory=list)
    articles: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "sections": self.sections,
            "acts": self.acts,
            "topics": self.topics,
            "courts": self.courts,
            "ipc_sections": self.ipc_sections,
            "bns_sections": self.bns_sections,
            "articles": self.articles,
            "confidence": self.confidence,
        }


# Known Indian legal acts (normalized names)
KNOWN_ACTS = {
    # Criminal law
    "indian penal code": "Indian Penal Code",
    "ipc": "Indian Penal Code",
    "bharatiya nyaya sanhita": "Bharatiya Nyaya Sanhita",
    "bns": "Bharatiya Nyaya Sanhita",
    "code of criminal procedure": "Code of Criminal Procedure",
    "crpc": "Code of Criminal Procedure",
    "bharatiya nagarik suraksha sanhita": "Bharatiya Nagarik Suraksha Sanhita",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita",
    "indian evidence act": "Indian Evidence Act",
    "evidence act": "Indian Evidence Act",
    "bharatiya sakshya adhiniyam": "Bharatiya Sakshya Adhiniyam",
    "bharatiya sakshya": "Bharatiya Sakshya Adhiniyam",
    # Civil law
    "code of civil procedure": "Code of Civil Procedure",
    "cpc": "Code of Civil Procedure",
    "transfer of property act": "Transfer of Property Act",
    "indian contract act": "Indian Contract Act",
    "contract act": "Indian Contract Act",
    "specific relief act": "Specific Relief Act",
    "limitation act": "Limitation Act",
    "indian succession act": "Indian Succession Act",
    "hindu succession act": "Hindu Succession Act",
    "hindu marriage act": "Hindu Marriage Act",
    "special marriage act": "Special Marriage Act",
    # Family law
    "hindu minority and guardianship act": "Hindu Minority and Guardianship Act",
    "muslim women protection of rights on divorce act": "Muslim Women Protection Act",
    # Constitutional law
    "constitution of india": "Constitution of India",
    "constitution": "Constitution of India",
    # Consumer protection
    "consumer protection act": "Consumer Protection Act",
    # NDPS
    "narcotic drugs and psychotropic substances act": "NDPS Act",
    "ndps act": "NDPS Act",
    "ndps": "NDPS Act",
    # Motor vehicles
    "motor vehicles act": "Motor Vehicles Act",
    # Labour law
    "industrial disputes act": "Industrial Disputes Act",
    "industrial disputes": "Industrial Disputes Act",
    "factories act": "Factories Act",
    "minimum wages act": "Minimum Wages Act",
    "payment of wages act": "Payment of Wages Act",
    "employees provident fund act": "Employees Provident Fund Act",
    # Cyber law
    "information technology act": "Information Technology Act",
    "it act": "Information Technology Act",
    # Anti-corruption
    "prevention of corruption act": "Prevention of Corruption Act",
    # Dowry
    "dowry prohibition act": "Dowry Prohibition Act",
    "dowry": "Dowry Prohibition Act",
    # Protection
    "protection of women from domestic violence act": "Domestic Violence Act",
    "domestic violence act": "Domestic Violence Act",
    # Juvenile
    "juvenile justice act": "Juvenile Justice Act",
    # Negotiable instruments
    "negotiable instruments act": "Negotiable Instruments Act",
    # Arbitration
    "arbitration and conciliation act": "Arbitration Act",
    # Trademark/Patent
    "trade marks act": "Trade Marks Act",
    "patents act": "Patents Act",
    # Environment
    "environment protection act": "Environment Protection Act",
    "forest act": "Forest Act",
    "wildlife protection act": "Wildlife Protection Act",
    # Arms
    "arms act": "Arms Act",
    # Family law additions
    "guardians and wards act": "Guardians and Wards Act",
    "indian divorce act": "Indian Divorce Act",
    "maintenance and welfare of parents and senior citizens act": "Maintenance Act",
    # Commercial law
    "competition act": "Competition Act",
    "companies act": "Companies Act",
    "limited liability partnership act": "LLP Act",
    "indian partnership act": "Indian Partnership Act",
    "sale of goods act": "Sale of Goods Act",
    # Property & registration
    "indian registration act": "Indian Registration Act",
    "indian stamps act": "Indian Stamps Act",
    "transfer of property act": "Transfer of Property Act",
    "easements act": "Easements Act",
    "indian trusts act": "Indian Trusts Act",
    "trusts act": "Indian Trusts Act",
    # RTI
    "right to information act": "Right to Information Act",
    "rti act": "Right to Information Act",
    # Legal services
    "legal services authorities act": "Legal Services Authorities Act",
    # Family courts
    "family courts act": "Family Courts Act",
    # Gram Nyayalayas
    "gram nyayalayas act": "Gram Nyayalayas Act",
    # Specific Relief
    "specific relief act": "Specific Relief Act",
    # Limitation
    "limitation act": "Limitation Act",
    # Copyright & IP
    "copyright act": "Copyright Act",
    "designs act": "Designs Act",
    "geographical indications act": "Geographical Indications Act",
    "semiconductor act": "Semiconductor Act",
    "biological diversity act": "Biological Diversity Act",
    "plant varieties act": "Plant Varieties Act",
    # Telecom
    "indian telegraph act": "Indian Telegraph Act",
    "indian wireless act": "Indian Wireless Act",
    # Cinematograph
    "cinematograph act": "Cinematograph Act",
    # Taxation
    "central goods and services tax act": "CGST Act",
    "state goods and services tax act": "SGST Act",
    "integrated goods and services tax act": "IGST Act",
    "customs act": "Customs Act",
    "finance act": "Finance Act",
    # Benami
    "benami transactions prohibition act": "Benami Act",
    # Black money
    "black money act": "Black Money Act",
    # IBC
    "insolvency and bankruptcy code": "IBC",
    "insolvency and bankruptcy code act": "IBC",
    # RERA
    "real estate regulation and development act": "RERA",
    # SEBI
    "securities and exchange board of india act": "SEBI Act",
    # NREGA
    "national rural employment guarantee act": "NREGA",
    # Juvenile
    "juvenile justice act": "Juvenile Justice Act",
    # Probation
    "probation of offenders act": "Probation Act",
    # Criminal tribunals
    "national security act": "NSA",
    "unlawful activities prevention act": "UAPA",
    "maharashtra control of organised crime act": "MCOCA",
    "prevention of money laundering act": "PMLA",
    "narcoics control bureau act": "NCB Act",
    # Child protection
    "commissions for protection of child rights act": "Child Rights Act",
    "protection of children from sexual offences act": "POCSO",
    "posco act": "POCSO",
    # Food safety
    "food safety and standards act": "Food Safety Act",
    # Telecommunications
    "indian telegraph act": "Indian Telegraph Act",
    # Inter-state
    "inter-state water disputes act": "Inter-State Water Disputes Act",
    # Indian penal code extensions
    "indian penal code 1860": "Indian Penal Code",
    "bharatiya nyaya sanhita 2023": "Bharatiya Nyaya Sanhita",
    # Evidence
    "indian evidence act 1872": "Indian Evidence Act",
}

# Common legal topics for query classification
LEGAL_TOPICS = {
    "bail": "bail",
    "anticipatory bail": "anticipatory_bail",
    "regular bail": "regular_bail",
    "default bail": "default_bail",
    "anticipbail": "anticipatory_bail",
    "arrest": "arrest",
    "fir": "fir",
    "first information report": "fir",
    "charge sheet": "charge_sheet",
    "chargesheet": "charge_sheet",
    "trial": "trial",
    "appeal": "appeal",
    "revision": "revision",
    "writ": "writ",
    "injunction": "injunction",
    "divorce": "divorce",
    "maintenance": "maintenance",
    "alimony": "alimony",
    "custody": "custody",
    "guardianship": "guardianship",
    "adoption": "adoption",
    "succession": "succession",
    "inheritance": "inheritance",
    "will": "will",
    "probate": "probate",
    "partition": "partition",
    "mortgage": "mortgage",
    "lease": "lease",
    "rent": "rent",
    "eviction": "eviction",
    "specific performance": "specific_performance",
    "breach of contract": "breach_of_contract",
    "damages": "damages",
    "compensation": "compensation",
    "recovery": "recovery",
    "execution": "execution",
    "decree": "decree",
    "judgment": "judgment",
    "order": "order",
    "sentence": "sentence",
    "punishment": "punishment",
    "penalty": "penalty",
    "fine": "fine",
    "imprisonment": "imprisonment",
    "death penalty": "death_penalty",
    "life imprisonment": "life_imprisonment",
    "parole": "parole",
    "remission": "remission",
    "pardon": "pardon",
    "forgery": "forgery",
    "fraud": "fraud",
    "cheating": "cheating",
    "defamation": "defamation",
    "criminal intimidation": "criminal_intimidation",
    "extortion": "extortion",
    "robbery": "robbery",
    "dacoity": "dacoity",
    "kidnapping": "kidnapping",
    "abduction": "abduction",
    "rape": "rape",
    "sexual assault": "sexual_assault",
    "molestation": "molestation",
    "harassment": "harassment",
    "stalking": "stalking",
    "dowry death": "dowry_death",
    "cruelty": "cruelty",
    "murder": "murder",
    "culpable homicide": "culpable_homicide",
    "accident": "accident",
    "drunk driving": "drunk_driving",
    "hit and run": "hit_and_run",
    "theft": "theft",
    "shoplifting": "shoplifting",
    "burglary": "burglary",
    "house breaking": "house_breaking",
    "criminal breach of trust": "criminal_breach_of_trust",
    "misappropriation": "misappropriation",
    "criminal trespass": "criminal_trespass",
    "nuisance": "nuisance",
    "trespass": "trespass",
}

# Court names
COURT_NAMES = {
    "supreme court": "Supreme Court of India",
    "high court": "High Court",
    "district court": "District Court",
    "sessions court": "Sessions Court",
    "metropolitan magistrate": "Metropolitan Magistrate",
    "judicial magistrate": "Judicial Magistrate",
    "executive magistrate": "Executive Magistrate",
    "family court": "Family Court",
    "consumer forum": "Consumer Forum",
    "national green tribunal": "National Green Tribunal",
    "nclt": "NCLT",
    "nclat": "NCLAT",
    "itat": "ITAT",
    "arbital tribunal": "Arbital Tribunal",
    "labour court": "Labour Court",
    "industrial tribunal": "Industrial Tribunal",
    "debt recovery tribunal": "Debt Recovery Tribunal",
}


class LegalQueryParser:
    """
    Extracts legal entities from user queries using deterministic regex patterns.
    Fast, no API calls, works offline.
    """

    # Regex patterns for entity extraction
    SECTION_PATTERNS = [
        # "Section 302 IPC" or "Section 302 of IPC"
        re.compile(r"section[s]?\s+(\d{1,4}[a-z]?)\s+(?:of\s+)?(ipc|bns|crpc|bnss)", re.IGNORECASE),
        # "Sections 302 and 376 IPC"
        re.compile(r"section[s]?\s+(\d{1,4}[a-z]?)\s+(?:and|,)\s+(\d{1,4}[a-z]?)\s+(ipc|bns|crpc|bnss)", re.IGNORECASE),
        # "Section 302" standalone
        re.compile(r"section[s]?\s+(\d{1,4}[a-z]?)", re.IGNORECASE),
        # "S. 302" or "Sec. 302"
        re.compile(r"(?:s|sec|sec\.|section)\.?\s*(\d{1,4}[a-z]?)", re.IGNORECASE),
        # Bracketed "[s 302]" or "[s. 302]"
        re.compile(r"\[s\.?\s*(\d{1,4}[a-z]?)\]", re.IGNORECASE),
    ]

    ARTICLE_PATTERNS = [
        # "Article 21" or "Article 21 of the Constitution"
        re.compile(r"article\s+(\d{1,4}[a-z]?)\s+(?:of\s+(?:the\s+)?constitution)?", re.IGNORECASE),
        # "Art. 21"
        re.compile(r"art\.?\s*(\d{1,4}[a-z]?)", re.IGNORECASE),
    ]

    ACT_PATTERN = re.compile(
        r"(?:" + "|".join(re.escape(k) for k in sorted(KNOWN_ACTS.keys(), key=len, reverse=True)) + r")",
        re.IGNORECASE,
    )

    TOPIC_PATTERN = re.compile(
        r"(?:" + "|".join(re.escape(k) for k in sorted(LEGAL_TOPICS.keys(), key=len, reverse=True)) + r")",
        re.IGNORECASE,
    )

    COURT_PATTERN = re.compile(
        r"(?:" + "|".join(re.escape(k) for k in sorted(COURT_NAMES.keys(), key=len, reverse=True)) + r")",
        re.IGNORECASE,
    )

    def parse(self, query: str) -> LegalEntities:
        """
        Parse a legal query and extract structured entities.
        
        Args:
            query: User's legal query text
            
        Returns:
            LegalEntities with extracted sections, acts, topics, courts
        """
        entities = LegalEntities()

        # Extract sections
        for pattern in self.SECTION_PATTERNS:
            matches = pattern.finditer(query)
            for match in matches:
                groups = match.groups()
                if len(groups) == 3:
                    # Multi-section pattern: "Sections 302 and 376 IPC"
                    sec1, sec2, act_hint = groups
                    for sec in (sec1, sec2):
                        sec_str = sec.strip().lower()
                        if act_hint.upper() == "IPC":
                            entities.ipc_sections.append(sec_str)
                        elif act_hint.upper() == "BNS":
                            entities.bns_sections.append(sec_str)
                        else:
                            entities.sections.append(sec_str)
                elif len(groups) == 2:
                    section_num, act_hint = groups
                    sec_str = section_num.strip().lower()
                    if act_hint.upper() == "IPC":
                        entities.ipc_sections.append(sec_str)
                    elif act_hint.upper() == "BNS":
                        entities.bns_sections.append(sec_str)
                    else:
                        entities.sections.append(sec_str)
                else:
                    section_num = groups[0]
                    sec_str = section_num.strip().lower()
                    entities.sections.append(sec_str)

        # Deduplicate sections
        entities.sections = list(dict.fromkeys(entities.sections))
        entities.ipc_sections = list(dict.fromkeys(entities.ipc_sections))
        entities.bns_sections = list(dict.fromkeys(entities.bns_sections))

        # Extract articles
        for pattern in self.ARTICLE_PATTERNS:
            matches = pattern.findall(query)
            for match in matches:
                entities.articles.append(match.lower())
        entities.articles = list(dict.fromkeys(entities.articles))

        # Extract acts
        act_matches = self.ACT_PATTERN.findall(query)
        for act_key in act_matches:
            normalized = act_key.lower().strip()
            if normalized in KNOWN_ACTS:
                act_name = KNOWN_ACTS[normalized]
                if act_name not in entities.acts:
                    entities.acts.append(act_name)

        # Extract topics
        topic_matches = self.TOPIC_PATTERN.findall(query)
        for topic_key in topic_matches:
            normalized = topic_key.lower().strip()
            if normalized in LEGAL_TOPICS:
                topic_name = LEGAL_TOPICS[normalized]
                if topic_name not in entities.topics:
                    entities.topics.append(topic_name)

        # Extract courts
        court_matches = self.COURT_PATTERN.findall(query)
        for court_key in court_matches:
            normalized = court_key.lower().strip()
            if normalized in COURT_NAMES:
                court_name = COURT_NAMES[normalized]
                if court_name not in entities.courts:
                    entities.courts.append(court_name)

        # Calculate confidence based on entities found
        entity_count = (
            len(entities.sections)
            + len(entities.ipc_sections)
            + len(entities.bns_sections)
            + len(entities.articles)
            + len(entities.acts)
            + len(entities.topics)
        )

        if entity_count == 0:
            entities.confidence = 0.0
        elif entity_count == 1:
            entities.confidence = 0.6
        elif entity_count == 2:
            entities.confidence = 0.8
        else:
            entities.confidence = min(0.95, 0.85 + (entity_count - 3) * 0.03)

        return entities

    def get_route_hint(self, entities: LegalEntities) -> Optional[str]:
        """
        Suggest a route based on extracted entities.
        Returns None if no confident hint.
        """
        # If we found acts, sections, or articles → LEGAL_RESEARCH
        if entities.acts or entities.sections or entities.ipc_sections or entities.bns_sections or entities.articles:
            return "LEGAL_RESEARCH"

        # If we found legal topics → still LEGAL_RESEARCH (with lower confidence)
        if entities.topics:
            return "LEGAL_RESEARCH"

        # If we found courts → LEGAL_RESEARCH
        if entities.courts:
            return "LEGAL_RESEARCH"

        return None

    def expand_query(self, entities: LegalEntities, original_query: str) -> str:
        """
        Expand the query with extracted entities for better retrieval.
        Adds act names, section context, and topic keywords.
        """
        expansions = []
        query_lower = original_query.lower()

        # Add act names if not already in query
        for act in entities.acts:
            if act.lower() not in query_lower:
                expansions.append(act)

        # Add section context (only if not already mentioned)
        for section in entities.sections:
            phrase = f"section {section}"
            if phrase not in query_lower:
                expansions.append(phrase)
        for section in entities.ipc_sections:
            phrase = f"section {section} ipc"
            if phrase not in query_lower:
                expansions.append(f"section {section} ipc")
        for section in entities.bns_sections:
            phrase = f"section {section} bns"
            if phrase not in query_lower:
                expansions.append(f"section {section} bns")

        # Add article context
        for article in entities.articles:
            phrase = f"article {article}"
            if phrase not in query_lower:
                expansions.append(f"article {article} constitution")

        # Add topic keywords
        for topic in entities.topics:
            topic_phrase = topic.replace("_", " ")
            if topic_phrase not in query_lower:
                expansions.append(topic_phrase)

        if expansions:
            expanded = original_query + " " + " ".join(expansions)
            return expanded

        return original_query


# Singleton for reuse
_parser_instance = None


def get_parser() -> LegalQueryParser:
    """Get or create the singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = LegalQueryParser()
    return _parser_instance


def parse_query(query: str) -> LegalEntities:
    """Convenience function to parse a query."""
    return get_parser().parse(query)


def expand_legal_query(query: str) -> str:
    """Convenience function to expand a query with extracted entities."""
    parser = get_parser()
    entities = parser.parse(query)
    return parser.expand_query(entities, query)
