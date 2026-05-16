"""
Contextual Response Generator for HECTOR.
Generates legally accurate, contextually rich responses with proper citations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


class ResponseFormat:
    """Output format options for generated responses."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    CITATIONS = "citations"


@dataclass
class LegalCitation:
    """Structured citation for legal references."""
    source: str
    page: str | None
    section: str
    act: str
    chapter: str | None = None
    paragraph: str | None = None


class ContextualResponseGenerator:
    """
    Generates contextually rich legal responses with:
    - Hierarchical context (Section → Chapter → Act)
    - Proper citation formatting
    - Multiple output formats
    - Related provisions suggestions
    """

    # Legal-specific system prompt for LLM-enhanced responses
    LEGAL_SYSTEM_PROMPT = """You are HECTOR, a legal research assistant specializing in Indian law.
Your responses must:
1. Cite sources with exact section numbers and page references
2. Use precise legal terminology
3. Include hierarchical context (Section within Chapter within Act)
4. Never hallucinate - only state what is in the source documents
5. Format citations as: [Source Name, Page X, Section Y Act]

When answering legal queries:
- Provide the relevant statutory text
- Include any exceptions or illustrations
- Note any amendments or recent changes
- Suggest related provisions that might be relevant"""

    def __init__(self, retriever: "HectorHybridRetriever"):
        self.retriever = retriever

    def generate(
        self,
        query: str,
        results: list[dict],
        format: str = ResponseFormat.SUMMARY,
        include_related: bool = True,
    ) -> dict:
        """
        Generate a formatted response from retrieval results.

        Args:
            query: The original user query
            results: List of retrieved document chunks
            format: Output format (summary, detailed, citations)
            include_related: Whether to include related provisions

        Returns:
            Dictionary with generated_response, citations, and related_provisions
        """
        if not results:
            return {
                "generated_response": "No results found for the given query.",
                "citations": [],
                "related_provisions": [],
            }

        citations = self._extract_citations(results)
        related = self._find_related_provisions(results) if include_related else []

        if format == ResponseFormat.CITATIONS:
            response = self._format_citations_only(citations)
        elif format == ResponseFormat.DETAILED:
            response = self._format_detailed(query, results, citations, related)
        else:  # SUMMARY
            response = self._format_summary(query, results, citations, related)

        return {
            "generated_response": response,
            "citations": [self._citation_to_dict(c) for c in citations],
            "related_provisions": related,
        }

    def _extract_citations(self, results: list[dict]) -> list[LegalCitation]:
        """Extract structured citations from retrieval results."""
        citations = []

        for item in results:
            metadata = item.get("metadata", {}) or {}
            citation = LegalCitation(
                source=metadata.get("source", "Unknown"),
                page=metadata.get("page"),
                section=metadata.get("section_number", ""),
                act=metadata.get("act_name", metadata.get("act", "")),
                chapter=metadata.get("chapter"),
            )
            citations.append(citation)

        return citations

    def _format_summary(
        self,
        query: str,
        results: list[dict],
        citations: list[LegalCitation],
        related: list[str],
    ) -> str:
        """Format results as a concise summary."""
        lines = []

        # Add relevant content from top results
        for item in results[:3]:
            doc = item.get("document", "")
            if doc:
                # Take first 300 chars of relevant content
                snippet = doc[:300].strip()
                if len(doc) > 300:
                    snippet += "..."
                lines.append(snippet)
                lines.append("")

        # Add citations
        if citations:
            lines.append("---")
            lines.append("**Citations:**")
            for cit in citations[:5]:
                cit_str = f"• {cit.act}"
                if cit.section:
                    cit_str += f" Section {cit.section}"
                if cit.page:
                    cit_str += f", Page {cit.page}"
                if cit.source and cit.source != "Unknown":
                    cit_str += f" ({cit.source})"
                lines.append(cit_str)

        # Add related provisions
        if related:
            lines.append("")
            lines.append("**Related Provisions:**")
            for rel in related[:5]:
                lines.append(f"• {rel}")

        return "\n".join(lines)

    def _format_detailed(
        self,
        query: str,
        results: list[dict],
        citations: list[LegalCitation],
        related: list[str],
    ) -> str:
        """Format results as detailed analysis with full context."""
        lines = []

        # Query context
        lines.append(f"**Query:** {query}")
        lines.append("")

        # Hierarchical context from top result
        if results:
            metadata = results[0].get("metadata", {}) or {}
            act = metadata.get("act_name") or metadata.get("act", "")
            chapter = metadata.get("chapter", "")
            section = metadata.get("section_number", "")
            section_title = metadata.get("section_title", "")

            if act:
                lines.append(f"**Act:** {act}")
            if chapter:
                lines.append(f"**Chapter:** {chapter}")
            if section:
                lines.append(f"**Section:** {section}" + (f" - {section_title}" if section_title else ""))
            lines.append("")

        # Full content from results
        lines.append("---")
        lines.append("**Relevant Legal Text:**")
        lines.append("")
        for i, item in enumerate(results[:5], 1):
            doc = item.get("document", "")
            if doc:
                lines.append(f"### Source {i}")
                lines.append(doc)
                lines.append("")

        # Detailed citations
        lines.append("---")
        lines.append("**Citations:**")
        for cit in citations:
            parts = [cit.act]
            if cit.chapter:
                parts.append(f"Chapter: {cit.chapter}")
            if cit.section:
                parts.append(f"Section {cit.section}")
            if cit.page:
                parts.append(f"Page {cit.page}")
            if cit.source and cit.source != "Unknown":
                parts.append(f"Source: {cit.source}")
            lines.append("• " + ", ".join(parts))

        # Related provisions
        if related:
            lines.append("")
            lines.append("**Related Provisions:**")
            for rel in related:
                lines.append(f"• {rel}")

        return "\n".join(lines)

    def _format_citations_only(self, citations: list[LegalCitation]) -> str:
        """Format as a pure citation list."""
        if not citations:
            return "No citations available."

        lines = ["**Citations:**", ""]
        for i, cit in enumerate(citations, 1):
            parts = [f"{i}. {cit.act}"]
            if cit.section:
                parts.append(f"Section {cit.section}")
            if cit.chapter:
                parts.append(f"Chapter: {cit.chapter}")
            if cit.page:
                parts.append(f"Page {cit.page}")
            if cit.source and cit.source != "Unknown":
                parts.append(f"({cit.source})")
            lines.append(" ".join(parts))

        return "\n".join(lines)

    def _find_related_provisions(self, results: list[dict]) -> list[str]:
        """Find related provisions based on metadata."""
        related = set()
        primary_act = None
        primary_chapter = None

        # Get primary context
        if results:
            metadata = results[0].get("metadata", {}) or {}
            primary_act = metadata.get("act_name") or metadata.get("act")
            primary_chapter = metadata.get("chapter")

        # Find related from other results
        for item in results[1:]:
            metadata = item.get("metadata", {}) or {}
            act = metadata.get("act_name") or metadata.get("act")
            section = metadata.get("section_number", "")
            chapter = metadata.get("chapter")

            # Same act, different chapter/section
            if act == primary_act and section:
                related.add(f"{act} Section {section}")

            # Same chapter, different section
            if chapter == primary_chapter and chapter and section:
                related.add(f"Section {section}")

        return list(related)[:10]

    def _citation_to_dict(self, citation: LegalCitation) -> dict:
        """Convert LegalCitation to dictionary."""
        return {
            "source": citation.source,
            "page": citation.page,
            "section": citation.section,
            "act": citation.act,
            "chapter": citation.chapter,
        }


def format_citation(source: str, page: str | None, section: str, act: str) -> str:
    """Format a single citation string."""
    parts = [f"Section {section} {act}"]
    if page:
        parts.append(f"Page {page}")
    if source and source != "Unknown":
        parts.append(f"({source})")
    return ", ".join(parts)