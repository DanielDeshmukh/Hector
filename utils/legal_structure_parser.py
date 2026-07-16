import re
from typing import Any


class LegalStructureParser:
    """
    Extracts hierarchical legal structure from Indian legal documents.

    Identifies: Act > Chapter > Part > Section > Sub-section > Clause > Paragraph
    """

    # Act-level patterns (e.g., "Bharatiya Nyaya Sanhita, 2023")
    ACT_PATTERN = re.compile(
        r"(Bharatiya\s+Nyaya\s+Sanhita|Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita"
        r"|Bharatiya\s+Sakshya\s+Adhiniyam|Indian\s+Penal\s+Code"
        r"|Code\s+of\s+Criminal\s+Procedure|Indian\s+Evidence\s+Act"
        r"|Code\s+of\s+Civil\s+Procedure|Constitution\s+of\s+India)"
        r"(?:\s*,?\s*\d{4})?",
        re.IGNORECASE,
    )

    # Chapter patterns (e.g., "CHAPTER V", "Chapter 5", "PART III")
    CHAPTER_PATTERN = re.compile(
        r"(?:^|\n)(?:CHAPTER|Chapter|PART|Part|Schedule|Appendix)\s+"
        r"(?:IV|III|II|I|V|VI|VII|VIII|IX|X|\d+|[A-Z]+)",
        re.IGNORECASE | re.MULTILINE,
    )

    # Section patterns (e.g., "Section 302", "302.", "s. 302")
    SECTION_PATTERN = re.compile(
        r"(?:^|\n)(?:Section|sec\.?|s\.)\s*(\d{1,4}[A-Z]?)"
        r"|(?:^|\n)(\d{1,4}[A-Z]?)\.\s",
        re.IGNORECASE | re.MULTILINE,
    )

    # Sub-section patterns (e.g., "(1)", "(a)", "(i)")
    SUBSECTION_PATTERN = re.compile(r"\(([a-zA-Z0-9]+)\)\s*([^\n(]+)", re.MULTILINE)

    # Clause pattern (e.g., "Provided that", "Provided also")
    PROVIDED_THAT_PATTERN = re.compile(
        r"(?:^|\n)\s*Provided\s+(?:that|also|further|nevertheless)",
        re.IGNORECASE | re.MULTILINE,
    )

    # Illustration pattern (e.g., "Illustration:", "Illustration (a)")
    ILLUSTRATION_PATTERN = re.compile(
        r"(?:^|\n)\s*Illustration(?:\s*\(?[a-zA-Z0-9]+\)?)?\s*:",
        re.IGNORECASE | re.MULTILINE,
    )

    # Exception pattern (e.g., "Exception 1:", "Exceptions:")
    EXCEPTION_PATTERN = re.compile(
        r"(?:^|\n)\s*Exception\s*:?\s*", re.IGNORECASE | re.MULTILINE
    )

    # Schedule/Appendix patterns
    SCHEDULE_PATTERN = re.compile(
        r"(?:^|\n)(?:THE\s+)?SCHEDULE\s*(?:TO|UNDER)?", re.IGNORECASE | re.MULTILINE
    )

    # Preamble/Title patterns
    PREAMBLE_PATTERN = re.compile(
        r"(?:^|\n)(?:PREAMBLE|Short\s+title|Extends\s+to)", re.IGNORECASE | re.MULTILINE
    )

    # Common Indian law act names and their abbreviations
    ACT_ALIASES = {
        "bharatiya nyaya sanhita": "BNS",
        "bharatiya nagarik suraksha sanhita": "BNSS",
        "bharatiya sakshya adhiniyam": "BSA",
        "indian penal code": "IPC",
        "code of criminal procedure": "CRPC",
        "indian evidence act": "IEA",
        "code of civil procedure": "CPC",
        "constitution of india": "Constitution",
    }

    # Map full names to abbreviations (for parsing matched text)
    ACT_FULL_TO_ABBREV = {
        "bharatiya nyaya sanhita": "BNS",
        "bharatiya nyaya sanhita, 2023": "BNS",
        "bharatiya nagarik suraksha sanhita": "BNSS",
        "bharatiya nagarik suraksha sanhita, 2023": "BNSS",
        "bharatiya sakshya adhiniyam": "BSA",
        "bharatiya sakshya adhiniyam, 2023": "BSA",
        "indian penal code": "IPC",
        "indian penal code, 1860": "IPC",
        "code of criminal procedure": "CRPC",
        "code of criminal procedure, 1973": "CRPC",
        "indian evidence act": "IEA",
        "indian evidence act, 1872": "IEA",
        "code of civil procedure": "CPC",
        "code of civil procedure, 1908": "CPC",
        "constitution of india": "Constitution",
        "constitution of india, 1950": "Constitution",
    }

    def __init__(self):
        self.current_act = None
        self.current_chapter = None
        self.current_part = None
        self.current_section = None

    def parse_document(self, text: str, source_filename: str = "") -> dict[str, Any]:
        """
        Extract complete hierarchical structure from document text.

        Returns:
            dict with keys: act, chapter, part, section, subsection,
                          has_illustration, has_exception, has_provided_that,
                          structure_type, parsed_elements
        """
        result = {
            "act": self._extract_act(text, source_filename),
            "chapter": self._extract_chapter(text),
            "part": self._extract_part(text),
            "section": self._extract_section(text),
            "subsection": self._extract_subsection(text),
            "has_illustration": bool(self.ILLUSTRATION_PATTERN.search(text)),
            "has_exception": bool(self.EXCEPTION_PATTERN.search(text)),
            "has_provided_that": bool(self.PROVIDED_THAT_PATTERN.search(text)),
            "has_schedule": bool(self.SCHEDULE_PATTERN.search(text)),
            "structure_type": self._determine_structure_type(text),
            "elements": {
                "sections": self._extract_all_sections(text),
                "chapters": self._extract_all_chapters(text),
                "provided_clauses": self._extract_provided_clauses(text),
                "illustrations": self._extract_illustrations(text),
                "exceptions": self._extract_exceptions(text),
            },
        }

        return result

    def _extract_act(self, text: str, filename: str = "") -> str | None:
        """Extract the Act name from text or filename."""
        # First try text
        match = self.ACT_PATTERN.search(text[:500])  # Check preamble
        if match:
            act_name = match.group(0).strip().lower()
            # Try full name mapping first
            if act_name in self.ACT_FULL_TO_ABBREV:
                return self.ACT_FULL_TO_ABBREV[act_name]
            # Fall back to aliases
            return self.ACT_ALIASES.get(act_name, match.group(0).strip())

        # Fall back to filename
        if filename:
            for alias, abbrev in self.ACT_ALIASES.items():
                if alias in filename.lower():
                    return abbrev

        return None

    def _extract_chapter(self, text: str) -> str | None:
        """Extract current chapter number/name."""
        match = re.search(
            r"(?:^|\n)(?:CHAPTER|Chapter)\s+(?:IV|III|II|I|V|VI|VII|VIII|IX|X|\d+|[A-Z]+)"
            r"(?:\s*[-–—:]\s*([^\n]+))?",
            text[:1000],
            re.IGNORECASE | re.MULTILINE,
        )
        if match:
            chapter = match.group(0).strip()
            if match.group(1):
                chapter += f" - {match.group(1).strip()}"
            return chapter
        return None

    def _extract_part(self, text: str) -> str | None:
        """Extract current Part number/name."""
        match = re.search(
            r"(?:^|\n)(?:PART|Part)\s+(?:IV|III|II|I|V|VI|VII|VIII|IX|X|\d+|[A-Z]+)"
            r"(?:\s*[-–—:]\s*([^\n]+))?",
            text[:1000],
            re.IGNORECASE | re.MULTILINE,
        )
        if match:
            return match.group(0).strip()
        return None

    def _extract_section(self, text: str) -> dict[str, str] | None:
        """Extract current section number and title."""
        # Pattern: "302.Whoever commits murder..."
        match = re.search(r"(\d{1,4}[A-Z]?)\.\s*([A-Z][^\n]{5,50})", text[:200])
        if match:
            return {"number": match.group(1), "title": match.group(2).strip()[:100]}

        # Pattern: "Section 302"
        match = re.search(
            r"(?:Section|sec\.?|s\.)\s*(\d{1,4}[A-Z]?)", text[:200], re.IGNORECASE
        )
        if match:
            return {"number": match.group(1), "title": None}

        return None

    def _extract_subsection(self, text: str) -> list[dict[str, str]]:
        """Extract sub-sections within the text."""
        subsections = []
        for match in self.SUBSECTION_PATTERN.finditer(text[:500]):
            subsections.append(
                {"label": match.group(1), "content": match.group(2).strip()[:100]}
            )
        return subsections

    def _extract_all_sections(self, text: str) -> list[dict[str, Any]]:
        """Extract all section references in the text."""
        sections = []
        for match in self.SECTION_PATTERN.finditer(text):
            section_num = match.group(1) or match.group(2)
            if section_num:
                sections.append({"number": section_num, "position": match.start()})
        return sections

    def _extract_all_chapters(self, text: str) -> list[dict[str, Any]]:
        """Extract all chapter references in the text."""
        chapters = []
        for match in re.finditer(
            r"(?:^|\n)(?:CHAPTER|Chapter)\s+([IVXLCDM\d]+)\s*[-–—:]*\s*([^\n]*)",
            text,
            re.IGNORECASE | re.MULTILINE,
        ):
            chapters.append(
                {
                    "number": match.group(1),
                    "title": match.group(2).strip()[:50] if match.group(2) else None,
                    "position": match.start(),
                }
            )
        return chapters

    def _extract_provided_clauses(self, text: str) -> list[str]:
        """Extract 'Provided that' clause content."""
        clauses = []
        for match in self.PROVIDED_THAT_PATTERN.finditer(text):
            # Get context after the match
            start = match.end()
            clause_text = text[start : start + 200].strip()
            if clause_text:
                clauses.append(clause_text[:100])
        return clauses

    def _extract_illustrations(self, text: str) -> list[str]:
        """Extract 'Illustration' content."""
        illustrations = []
        for match in self.ILLUSTRATION_PATTERN.finditer(text):
            start = match.end()
            illust_text = text[start : start + 300].strip()
            if illust_text:
                illustrations.append(illust_text[:150])
        return illustrations

    def _extract_exceptions(self, text: str) -> list[str]:
        """Extract 'Exception' content."""
        exceptions = []
        for match in self.EXCEPTION_PATTERN.finditer(text):
            start = match.end()
            except_text = text[start : start + 200].strip()
            if except_text:
                exceptions.append(except_text[:100])
        return exceptions

    def _determine_structure_type(self, text: str) -> str:
        """Determine the document structure type."""
        text_lower = text[:500].lower()

        if "preamble" in text_lower and "short title" in text_lower:
            return "bare_act"
        if "chapter" in text_lower:
            return "commentary"
        if "schedule" in text_lower:
            return "schedule"
        if "appendix" in text_lower:
            return "appendix"
        if "illustration" in text_lower:
            return "commentary"

        return "general_legal_text"

    def infer_act_from_filename(self, filename: str) -> str | None:
        """Infer Act name from PDF filename."""
        filename_lower = filename.lower()
        for alias, abbrev in self.ACT_ALIASES.items():
            if alias in filename_lower:
                return abbrev

        # Handle common patterns
        if "bns" in filename_lower:
            return "BNS"
        if "bnss" in filename_lower:
            return "BNSS"
        if "bsa" in filename_lower:
            return "BSA"
        if "ipc" in filename_lower:
            return "IPC"
        if "crpc" in filename_lower:
            return "CRPC"

        return None


def extract_real_act_name(text: str, filename: str = "") -> str | None:
    """
    Extract the real act name from Indian legal document text.

    Scans the first 2000 characters for patterns like:
      - "THE LIMITATION ACT, 1963"
      - "ACT NO. 36 OF 1963"
      - "The Indian Contract Act, 1872"

    Returns the cleaned act name (e.g., "Limitation Act, 1963") or None.
    """
    # Manual overrides for known mislabelled PDFs (filename -> correct act name)
    OVERRIDES = {
        "Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "Bharatiya_Nyaya_Sanhita_2023.pdf": "Bharatiya Nyaya Sanhita, 2023",
        "Bharatiya_Sakshya_Adhiniyam_2023.pdf": "Bharatiya Sakshya Adhiniyam, 2023",
        "Code_of_Criminal_Procedure_1973.pdf": "Code of Criminal Procedure, 1973",
        "fixed_The_Code_of_Criminal.pdf": "Code of Criminal Procedure, 1973",
        "Code_Of_Civil_Procedure_1908.pdf": "Code of Civil Procedure, 1908",
        "Code_Of_Civil_Procedure_1908_v2.pdf": "Code of Civil Procedure, 1908",
        "Indian_Penal_Code_1860.pdf": "Indian Penal Code, 1860",
        "Information_Technology_Act_2000.pdf": "Information Technology Act, 2000",
        "Competition_Act_2002.pdf": "Competition Act, 2002",
        "Environment_Protection_Act_1986.pdf": "Environment Protection Act, 1986",
        "Factories_Act_1948.pdf": "Factories Act, 1948",
        "Forest_Act_1927.pdf": "Forest Act, 1927",
        "Industrial_Disputes_Act_1947.pdf": "Industrial Disputes Act, 1947",
        "Hindu_Marriage_Act_1955.pdf": "Hindu Marriage Act, 1955",
        "Hindu_Minority_And_Guardianship_Act_1956.pdf": "Hindu Minority and Guardianship Act, 1956",
        "Hindu_Succession_Act_1956.pdf": "Hindu Succession Act, 1956",
        "Copyright_Act_1957.pdf": "Copyright Act, 1957",
        "Trusts_Act_1882.pdf": "Indian Trusts Act, 1882",
        "Easements_Act_1882.pdf": "Easements Act, 1882",
        "Dowry_Prohibition_Act_1961.pdf": "Dowry Prohibition Act, 1961",
        "Right_To_Information_Act_2005.pdf": "Right to Information Act, 2005",
        "Arbitration_and_Conciliation_Act_1996.pdf": "Arbitration and Conciliation Act, 1996",
        "Arms_Act_1959.pdf": "Arms Act, 1959",
        "Consumer_Protection_Act_2019.pdf": "Consumer Protection Act, 2019",
        "Legal_Services_Authorities_Act_1987.pdf": "Legal Services Authorities Act, 1987",
        "Limitation_Act_1963.pdf": "Limitation Act, 1963",
        "Motor_Vehicles_Act_1988.pdf": "Motor Vehicles Act, 1988",
        "Negotiable_Instruments_Act_1881.pdf": "Negotiable Instruments Act, 1881",
        "Prevention_of_Corruption_Act_1988.pdf": "Prevention of Corruption Act, 1988",
        "Protection_of_Women_from_Domestic_Violence_Act_2005.pdf": "Protection of Women from Domestic Violence Act, 2005",
        "Specific_Relief_Act_1963.pdf": "Specific Relief Act, 1963",
        "Transfer_of_Property_Act_1882.pdf": "Transfer of Property Act, 1882",
        "Indian_Contract_Act_1872.pdf": "Indian Contract Act, 1872",
        "Indian_Evidence_Act_1872.pdf": "Indian Evidence Act, 1872",
        "Juvenile_Justice_Act_2015.pdf": "Juvenile Justice Act, 2015",
        "Gram_Nyayalayas_Act_2008.pdf": "Gram Nyayalayas Act, 2008",
        "Family_Courts_Act_1984.pdf": "Family Courts Act, 1984",
        "Narcotic_Drugs_and_Psychotropic_Substances_Act_1985.pdf": "Narcotic Drugs and Psychotropic Substances Act, 1985",
        "Constitution_of_India.pdf": "Constitution of India",
    }
    if filename in OVERRIDES:
        return OVERRIDES[filename]

    search_text = text[:2000]

    # Pattern 1: "THE <NAME> ACT, <YEAR>" — most common title pattern
    m = re.search(
        r"THE\s+([\w\s]+?)\s+ACT[,\s]+(\d{4})",
        search_text,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        # Clean up: remove leading numbers, extra whitespace
        name = re.sub(r"^\d+\s*", "", name).strip()
        if name:
            return f"{name} Act, {year}"

    # Pattern 2: "<NAME> Act, <YYYY>" (title case)
    m = re.search(
        r"((?:[A-Z][a-z]+\s+)+)Act[,\s]+(\d{4})",
        search_text,
    )
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        return f"{name}Act, {year}"

    # Pattern 3: "ACT NO. <X> OF <YEAR>" — extract year, look for name nearby
    m = re.search(r"ACT\s+NO\.?\s*\d+\s+OF\s+(\d{4})", search_text, re.IGNORECASE)
    if m:
        year = m.group(1)
        # Try to find the act name in surrounding text
        name_match = re.search(
            r"(?:An\s+Act\s+to\s+consolidate\s+and\s+amend\s+the\s+law\s+for\s+)?"
            r"the\s+([\w\s]+?)\s*(?:,?\s*\d{4}|\.?\s*BE\s+it)",
            search_text,
            re.IGNORECASE,
        )
        if name_match:
            name = name_match.group(1).strip()
            name = re.sub(r"\s+", " ", name)
            return f"{name} Act, {year}"
        return f"Act of {year}"

    # Pattern 4: Look for THE <NAME> ACT pattern more broadly
    # Search only first 800 chars (title page area) to avoid false matches
    m = re.search(
        r"THE\s+([\w\s]{3,60}?)\s+ACT[,\s]+(\d{4})",
        search_text[:800],
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        name = re.sub(r"^\d+\s*", "", name).strip()
        name = re.sub(r"\s+", " ", name)
        if name and len(name) > 2:
            return f"{name} Act, {year}"

    # Pattern 5: Look for known act names in first 1500 chars
    known_acts = [
        ("Copyright", "Copyright Act, 1957"),
        ("Commissions for Protection of Child Rights", "Commissions for Protection of Child Rights Act, 2005"),
        ("Tripura University", "Tripura University Act, 2006"),
        ("Indian Maritime University", "Indian Maritime University Act, 2008"),
        ("National Highways", "National Highways Act, 1956"),
        ("Advocates", "Advocates Act, 1961"),
        ("Nagaland University", "Nagaland University Act, 1989"),
        ("Oaths", "Oaths Act, 1969"),
        ("Uttar Pradesh Technical University", "UP Technical University Act, 2000"),
        ("Food Safety and Standards", "Food Safety and Standards Act, 2006"),
        ("Tamil Nadu Panchayat", "Tamil Nadu Panchayat Act, 1994"),
        ("Punjab Tenancy", "Punjab Tenancy Act, 1887"),
        ("National Rural Employment Guarantee", "NREGA, 2005"),
        ("Bihar Reorganisation", "Bihar Reorganisation Act, 2000"),
        ("Negotiable Instruments", "Negotiable Instruments Act, 1881"),
        ("Specific Relief", "Specific Relief Act, 1963"),
        ("Motor Vehicles", "Motor Vehicles Act, 1988"),
        ("Narcotic Drugs and Psychotropic Substances", "NDPS Act, 1985"),
        ("Arbitration and Conciliation", "Arbitration and Conciliation Act, 1996"),
        ("Indian Contract", "Indian Contract Act, 1872"),
        ("Transfer of Property", "Transfer of Property Act, 1882"),
        ("Limitation", "Limitation Act, 1963"),
        ("Legal Services Authorities", "Legal Services Authorities Act, 1987"),
        ("Consumer Protection", "Consumer Protection Act, 2019"),
        ("Indian Penal Code", "Indian Penal Code, 1860"),
        ("Bharatiya Nyaya Sanhita", "Bharatiya Nyaya Sanhita, 2023"),
        ("Bharatiya Nagarik Suraksha Sanhita", "Bharatiya Nagarik Suraksha Sanhita, 2023"),
        ("Bharatiya Sakshya Adhiniyam", "Bharatiya Sakshya Adhiniyam, 2023"),
        ("Code of Criminal Procedure", "Code of Criminal Procedure, 1973"),
        ("Code of Civil Procedure", "Code of Civil Procedure, 1908"),
        ("Indian Evidence", "Indian Evidence Act, 1872"),
        ("Constitution of India", "Constitution of India"),
    ]
    lower_text = search_text[:1500].lower()
    for keyword, act_name in known_acts:
        if keyword.lower() in lower_text:
            return act_name

    # Fall back to filename
    if filename:
        # Convert filename to readable name
        name = filename.replace(".pdf", "").replace(".PDF", "")
        name = name.replace("_", " ")
        # Try to extract year
        year_match = re.search(r"(\d{4})", name)
        if year_match:
            year = year_match.group(1)
            name = re.sub(r"\s*\d{4}\s*$", "", name).strip()
            name = re.sub(r"\s+", " ", name)
            return f"{name}, {year}"
        return name

    return None


class MetadataEnricher:
    """
    Enriches document metadata with legal structure information.
    """

    @staticmethod
    def enrich_metadata(
        base_metadata: dict, structure: dict, source_filename: str
    ) -> dict:
        """
        Combine base metadata with extracted legal structure.

        Returns enriched metadata with:
        - act_name, chapter, section_number, section_title
        - is_bns, is_ipc, is_repealed
        - effective_date (where applicable)
        - jurisdiction indicators
        """
        enriched = dict(base_metadata)

        # Add legal structure fields
        # Use real_act_name (extracted from PDF content) as primary act identifier
        real_act = structure.get("real_act_name")
        if real_act:
            enriched["act_name"] = real_act
            enriched["real_act_name"] = real_act
        elif structure.get("act"):
            enriched["act_name"] = structure["act"]

        if structure.get("chapter"):
            enriched["chapter"] = structure["chapter"]

        if structure.get("part"):
            enriched["part"] = structure["part"]

        # Section info
        if structure.get("section"):
            section = structure["section"]
            if section.get("number") is not None:
                enriched["section_number"] = section.get("number")
            if section.get("title") is not None:
                enriched["section_title"] = section.get("title")

        # Legal indicators
        act = structure.get("act", "") or ""
        if act:
            enriched["is_bns"] = "BNS" in act.upper()
            enriched["is_ipc"] = "IPC" in act.upper()
            enriched["is_bnss"] = "BNSS" in act.upper()
            enriched["is_bsa"] = "BSA" in act.upper()

        # Check for repealed statutes (IPC effective until July 1, 2024)
        if enriched.get("is_ipc"):
            enriched["is_repealed"] = True
            enriched["effective_date"] = "1860-01-01"
            enriched["replaced_by"] = "BNS (w.e.f. 2024-07-01)"

        # BNS/BNSS/BSA are current laws
        if enriched.get("is_bns") or enriched.get("is_bnss") or enriched.get("is_bsa"):
            enriched["is_repealed"] = False
            enriched["effective_date"] = "2024-07-01"

        # Structure type
        enriched["structure_type"] = structure.get("structure_type", "general")

        # Feature flags
        enriched["has_illustration"] = structure.get("has_illustration", False)
        enriched["has_exception"] = structure.get("has_exception", False)
        enriched["has_provided_that"] = structure.get("has_provided_that", False)
        enriched["has_schedule"] = structure.get("has_schedule", False)

        # Remove None values and convert non-scalar types (ChromaDB rejects them)
        clean = {}
        for k, v in enriched.items():
            if v is None:
                continue
            # ChromaDB only accepts str, int, float, bool scalars
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, (list, tuple)):
                clean[k] = ", ".join(str(item) for item in v)
            elif isinstance(v, set):
                clean[k] = ", ".join(sorted(str(item) for item in v))
            elif isinstance(v, dict):
                clean[k] = str(v)
            else:
                clean[k] = str(v)

        return clean


def test_parser():
    """Quick test of the legal structure parser."""
    parser = LegalStructureParser()

    test_texts = [
        """
        Bharatiya Nyaya Sanhita, 2023

        CHAPTER I - PRELIMINARY

        Short title. 1. (1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.

        (2) It shall extend to the whole of India.

        Definition. 2. In this Act, unless the context otherwise requires, "State" includes
        a Union territory.

        101. Whoever commits murder shall be punished with death or imprisonment for life.

        Illustration: A shoots Z with the intention of killing him.
        Provided that the court may award lesser punishment.
        """,
        """
        Section 302 IPC

        Whoever commits murder shall be punished with death or imprisonment for life,
        and shall also be liable to fine.
        """,
    ]

    for i, text in enumerate(test_texts):
        print(f"\n{'=' * 50}")
        print(f"Test {i + 1}:")
        print("=" * 50)
        result = parser.parse_document(text, f"test_{i + 1}.pdf")
        print(f"Act: {result['act']}")
        print(f"Chapter: {result['chapter']}")
        print(f"Section: {result['section']}")
        print(f"Has illustrations: {result['has_illustration']}")
        print(f"Has 'provided that': {result['has_provided_that']}")
        print(f"Structure type: {result['structure_type']}")


if __name__ == "__main__":
    test_parser()
