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
        "code of criminal procedure": "CRPC",
        "indian evidence act": "IEA",
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
        if structure.get("act"):
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
