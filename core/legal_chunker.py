"""
HECTOR Section-Aware Legal Chunker

Splits Indian legal text at section boundaries (not token count).
Each section becomes its own chunk with denormalized context.

Chunk format:
    [Act Name, Year | Chapter X: Chapter Title | Section N: Section Title]
    Section text with sub-sections, provisos, exceptions...
"""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class LegalSection:
    """A parsed legal section with its content."""

    act_name: str = ""
    chapter: str = ""
    section_number: str = ""
    section_title: str = ""
    content: str = ""
    has_proviso: bool = False
    has_exception: bool = False
    has_illustration: bool = False


# Patterns for splitting
SECTION_SPLIT_PATTERN = re.compile(
    r"(?:^|\n)(?:Section|sec\.?|s\.)\s*(\d{1,4}[A-Z]?)\.?\s+"
    r"|(?:^|\n)(\d{1,4}[A-Z]?)\.\s+[^a-z\d]",
    re.IGNORECASE | re.MULTILINE,
)

CHAPTER_SPLIT_PATTERN = re.compile(
    r"(?:^|\n)(?:CHAPTER|Chapter)\s+"
    r"(?:IV|III|II|I|V|VI|VII|VIII|IX|X|\d+|[A-Z]+)[:\s]+([^\n]*)",
    re.IGNORECASE | re.MULTILINE,
)

PROVIDED_THAT_PATTERN = re.compile(
    r"(?:^|\n)\s*Provided\s+(?:that|also|further|nevertheless)",
    re.IGNORECASE | re.MULTILINE,
)

EXCEPTION_PATTERN = re.compile(
    r"(?:^|\n)\s*Exception\s*:?\s*",
    re.IGNORECASE | re.MULTILINE,
)

ILLUSTRATION_PATTERN = re.compile(
    r"(?:^|\n)\s*Illustration(?:\s*\(?[a-zA-Z0-9]+\)?)?\s*:",
    re.IGNORECASE | re.MULTILINE,
)

SUBSECTION_PATTERN = re.compile(
    r"\(([a-zA-Z0-9]+)\)\s+",
    re.MULTILINE,
)


class SectionAwareChunker:
    """
    Splits legal text at section boundaries.

    Each section becomes its own chunk with denormalized context prepended.
    Handles:
    - Section-level splitting (never splits mid-section)
    - Sub-section boundaries for very long sections
    - Provisos/exceptions kept with parent section
    - Denormalized context (Act|Chapter|Section) prepended to chunk
    - Cross-section bleed detection: rejects chunks that reference wrong sections
    """

    # Maximum section length before splitting at sub-sections
    MAX_SECTION_CHARS = 4000

    # Minimum section length (merge with next if shorter)
    # Set low to avoid merging real sections — only merge truly empty stubs
    MIN_SECTION_CHARS = 30

    # Regex to detect section references within chunk text
    # Matches "Section 123" or "Sec 123" or "s. 123" in body text
    _SECTION_REF_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:Section|sec\.?|s\.)\s*(\d{1,4}[A-Z]?)\.?\s+",
        re.IGNORECASE | re.MULTILINE,
    )

    def __init__(self):
        self.current_act = ""
        self.current_chapter = ""
        self.current_part = ""

    def chunk_page(
        self,
        text: str,
        act_name: str = "",
        chapter: str = "",
    ) -> List[dict]:
        """
        Split a page of legal text into section-level chunks.

        Args:
            text: Raw text from a PDF page (OCR or extracted)
            act_name: Detected act name (e.g., "Indian Penal Code")
            chapter: Detected chapter (e.g., "Chapter XVII")

        Returns:
            List of dicts with keys: content, section_number, section_title,
            has_proviso, has_exception, has_illustration
        """
        if not text or not text.strip():
            return []

        self.current_act = act_name
        self.current_chapter = chapter

        # Find all section boundaries
        boundaries = self._find_section_boundaries(text)

        if not boundaries:
            # No sections found — treat entire text as one chunk
            return [
                {
                    "content": text.strip(),
                    "section_number": "",
                    "section_title": "",
                    "has_proviso": bool(PROVIDED_THAT_PATTERN.search(text)),
                    "has_exception": bool(EXCEPTION_PATTERN.search(text)),
                    "has_illustration": bool(ILLUSTRATION_PATTERN.search(text)),
                }
            ]

        # Split text at boundaries
        sections = []
        for i, (start, end, section_num, section_title) in enumerate(boundaries):
            section_text = text[start:end].strip()
            if not section_text:
                continue

            # Check if section is too long — split at sub-sections
            if len(section_text) > self.MAX_SECTION_CHARS:
                sub_chunks = self._split_long_section(section_text)
                for sub_text in sub_chunks:
                    sections.append(
                        {
                            "content": sub_text,
                            "section_number": section_num,
                            "section_title": section_title,
                            "has_proviso": bool(PROVIDED_THAT_PATTERN.search(sub_text)),
                            "has_exception": bool(EXCEPTION_PATTERN.search(sub_text)),
                            "has_illustration": bool(
                                ILLUSTRATION_PATTERN.search(sub_text)
                            ),
                        }
                    )
            else:
                sections.append(
                    {
                        "content": section_text,
                        "section_number": section_num,
                        "section_title": section_title,
                        "has_proviso": bool(PROVIDED_THAT_PATTERN.search(section_text)),
                        "has_exception": bool(EXCEPTION_PATTERN.search(section_text)),
                        "has_illustration": bool(
                            ILLUSTRATION_PATTERN.search(section_text)
                        ),
                    }
                )

        # Merge very short sections with next
        merged = self._merge_short_sections(sections)

        # Add denormalized context to each chunk
        for section in merged:
            section["content"] = self._add_context_prefix(
                section["content"],
                section["section_number"],
                section["section_title"],
            )

        return merged

    def _find_section_boundaries(self, text: str) -> List[Tuple[int, int, str, str]]:
        """
        Find all section boundaries in text.
        Returns list of (start, end, section_number, section_title) tuples.
        """
        matches = list(SECTION_SPLIT_PATTERN.finditer(text))
        if not matches:
            return []

        boundaries = []
        for i, match in enumerate(matches):
            # Start is the beginning of this section header
            start = match.start()

            # End is the start of the next section header (or end of text)
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            # Extract section number
            section_num = match.group(1) or match.group(2) or ""

            # Extract section title (text after section number, before first newline)
            section_text = text[start:end]
            section_title = ""
            title_match = re.search(
                r"(?:Section|sec\.?|s\.)\s*\d{1,4}[A-Z]?\.?\s*(.+?)(?:\n|$)",
                section_text,
                re.IGNORECASE,
            )
            if title_match:
                section_title = title_match.group(1).strip()
                # Clean up common prefixes
                section_title = re.sub(
                    r"^(?:of|for|in|on|by|with)\s+",
                    "",
                    section_title,
                    flags=re.IGNORECASE,
                )

            boundaries.append((start, end, section_num, section_title))

        return boundaries

    def _split_long_section(self, text: str) -> List[str]:
        """Split a very long section at sub-section boundaries."""
        # Find sub-section boundaries
        subsection_matches = list(SUBSECTION_PATTERN.finditer(text))

        if not subsection_matches:
            # No sub-sections — fall back to paragraph splitting
            return self._split_at_paragraphs(text)

        chunks = []
        for i, match in enumerate(subsection_matches):
            start = match.start()
            end = (
                subsection_matches[i + 1].start()
                if i + 1 < len(subsection_matches)
                else len(text)
            )

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks if chunks else [text]

    def _split_at_paragraphs(self, text: str) -> List[str]:
        """Split text at paragraph boundaries (double newlines)."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.MAX_SECTION_CHARS:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _merge_short_sections(self, sections: List[dict]) -> List[dict]:
        """Merge very short sections with the next section, avoiding cross-section bleed."""
        if not sections:
            return []

        merged = []
        i = 0

        while i < len(sections):
            current = sections[i]

            # Check if this section is too short and has a next section
            if len(current["content"]) < self.MIN_SECTION_CHARS and i + 1 < len(
                sections
            ):
                next_section = sections[i + 1]
                # Only merge if the short section doesn't introduce cross-section refs
                other_refs = self._find_other_section_refs(
                    current["content"], current["section_number"]
                )
                if not other_refs:
                    # Merge with next
                    merged_text = current["content"] + "\n\n" + next_section["content"]
                    sections[i + 1] = {
                        "content": merged_text,
                        "section_number": next_section["section_number"]
                        or current["section_number"],
                        "section_title": next_section["section_title"]
                        or current["section_title"],
                        "has_proviso": current["has_proviso"]
                        or next_section["has_proviso"],
                        "has_exception": current["has_exception"]
                        or next_section["has_exception"],
                        "has_illustration": current["has_illustration"]
                        or next_section["has_illustration"],
                    }
                else:
                    merged.append(current)
                i += 1
            else:
                merged.append(current)
                i += 1

        return merged

    def _find_other_section_refs(self, text: str, own_section: str) -> List[str]:
        """
        Find section references in text that don't match the chunk's own section.
        Returns list of foreign section numbers found (empty = safe to merge).
        """
        refs = set()
        for m in self._SECTION_REF_PATTERN.finditer(text):
            ref = m.group(1)
            if ref != own_section:
                refs.add(ref)
        return sorted(refs)

    def _add_context_prefix(
        self, content: str, section_number: str, section_title: str
    ) -> str:
        """
        Prepend denormalized context to chunk content.
        This helps dense embeddings retrieve the right section.

        Format: [Act Name | Chapter X: Chapter Title | Section N: Section Title]
        """
        parts = []

        # Act name
        if self.current_act:
            parts.append(self.current_act)

        # Chapter
        if self.current_chapter:
            parts.append(self.current_chapter)

        # Section
        if section_number:
            section_label = f"Section {section_number}"
            if section_title:
                section_label += f": {section_title}"
            parts.append(section_label)

        if not parts:
            return content

        prefix = " | ".join(parts)
        return f"[{prefix}]\n{content}"


# Convenience function
def chunk_legal_page(
    text: str,
    act_name: str = "",
    chapter: str = "",
) -> List[dict]:
    """Chunk a page of legal text into section-level chunks."""
    chunker = SectionAwareChunker()
    return chunker.chunk_page(text, act_name, chapter)
