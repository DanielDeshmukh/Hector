"""
Contextual Response Generator for HECTOR.
Generates legally accurate, contextually rich responses with proper citations.
"""

from __future__ import annotations
from dataclasses import dataclass
import re
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
        citations = self._extract_citations(results)
        related = self._find_related_provisions(results) if include_related else []
        structured = self._build_legal_rag_payload(results)
        response = self._format_legal_rag(query, results, related)

        return {
            "generated_response": response,
            "answer_sections": structured["answer_sections"],
            "source_sections": structured["source_sections"],
            "answer_confidence": structured["answer_confidence"],
            "citations": [self._citation_to_dict(c) for c in citations],
            "related_provisions": related,
        }

    def _build_legal_rag_payload(self, results: list[dict]) -> dict:
        if not results:
            return {
                "answer_sections": [
                    {
                        "title": "Result",
                        "body": "No relevant sources found for this query.",
                        "rows": [],
                    }
                ],
                "source_sections": [],
                "answer_confidence": 0.0,
            }

        sources = [
            self._source_payload(item, index, len(results))
            for index, item in enumerate(results, start=1)
        ]
        ipc_sources = [source for source in sources if source["act"] == "IPC"]
        bns_sources = [source for source in sources if source["act"] == "BNS"]

        overview_lines = []
        if ipc_sources:
            source = self._best_source(ipc_sources)
            overview_lines.append(
                f"Indian Penal Code, 1860 [IPC]: {self._framework_sentence(source)} [S{source['number']}]"
            )
        else:
            overview_lines.append(
                "Indian Penal Code, 1860 [IPC]: No directly retrieved IPC chunk supports an answer for this query."
            )

        if bns_sources:
            source = self._best_source(bns_sources)
            overview_lines.append(
                f"Bharatiya Nyaya Sanhita, 2023 [BNS]: {self._framework_sentence(source)} [S{source['number']}]"
            )
        else:
            overview_lines.append(
                "Bharatiya Nyaya Sanhita, 2023 [BNS]: No directly retrieved BNS chunk supports an answer for this query."
            )

        if ipc_sources and bns_sources:
            ipc = self._best_source(ipc_sources)
            bns = self._best_source(bns_sources)
            overview_lines.append(
                f"Key difference: the retrieved IPC source is centred on Section {ipc['section']} IPC, while the retrieved BNS source is centred on Section {bns['section']} BNS. [S{ipc['number']}] [S{bns['number']}]"
            )

        comparison_rows = [
            {
                "point": "Section reference",
                "ipc": self._table_section(ipc_sources, "IPC"),
                "bns": self._table_section(bns_sources, "BNS"),
            },
            {
                "point": "Simple/basic offence punishment",
                "ipc": self._table_punishment(ipc_sources),
                "bns": self._table_punishment(bns_sources),
            },
            {
                "point": "Repeat/aggravated offence punishment",
                "ipc": self._table_aggravated(ipc_sources),
                "bns": self._table_aggravated(bns_sources),
            },
            {
                "point": "Cognisable status",
                "ipc": self._table_status(ipc_sources),
                "bns": self._table_status(bns_sources),
            },
        ]

        return {
            "answer_sections": [
                {
                    "title": "Grounded Answer",
                    "body": "\n".join(overview_lines),
                    "rows": [],
                },
                {
                    "title": "Comparison",
                    "body": "",
                    "rows": comparison_rows,
                },
            ],
            "source_sections": sources,
            "answer_confidence": float(self._answer_confidence(sources)),
        }

    def _format_legal_rag(
        self, query: str, results: list[dict], related: list[str]
    ) -> str:
        """Format a response using the HECTOR Research Report format."""
        if not results:
            return (
                f"[HECTOR Intelligence Report] · [0 sources retrieved] · Query: {query}\n\n"
                "No relevant sources found for this query.\n\n"
                "RETRIEVED SOURCES\n\n"
                "Answer confidence: 0% Low confidence — retrieved sources may not fully cover this query.\n\n"
                "Note: This information is provided for research purposes and does not constitute formal legal advice."
            )

        sources = [
            self._source_payload(item, index, len(results))
            for index, item in enumerate(results, start=1)
        ]
        ipc_sources = [source for source in sources if source["act"] == "IPC"]
        bns_sources = [source for source in sources if source["act"] == "BNS"]

        lines = [
            f"[HECTOR Intelligence Report] · [{len(sources)} sources retrieved] · Query: {query}",
            "",
        ]

        if ipc_sources:
            source = self._best_source(ipc_sources)
            lines.append(
                f"**Indian Penal Code, 1860** [IPC]: {self._framework_sentence(source)} [§{source['number']}]"
            )
        else:
            lines.append(
                "**Indian Penal Code, 1860** [IPC]: No directly retrieved IPC chunk supports an answer for this query."
            )

        if bns_sources:
            source = self._best_source(bns_sources)
            lines.append(
                f"**Bharatiya Nyaya Sanhita, 2023** [BNS]: {self._framework_sentence(source)} [§{source['number']}]"
            )
        else:
            lines.append(
                "**Bharatiya Nyaya Sanhita, 2023** [BNS]: No directly retrieved BNS chunk supports an answer for this query."
            )

        if ipc_sources and bns_sources:
            ipc = self._best_source(ipc_sources)
            bns = self._best_source(bns_sources)
            lines.append(
                f"Key difference: the retrieved IPC source is centred on Section {ipc['section']} IPC, while the retrieved BNS source is centred on Section {bns['section']} BNS. [§{ipc['number']}] [§{bns['number']}]"
            )

        lines.extend(
            [
                "",
                "| Comparison point | Indian Penal Code, 1860 [IPC] | Bharatiya Nyaya Sanhita, 2023 [BNS] |",
            ]
        )
        lines.append("| --- | --- | --- |")
        lines.append(
            f"| Section reference (definition) | {self._table_section(ipc_sources, 'IPC')} | {self._table_section(bns_sources, 'BNS')} |"
        )
        lines.append(
            f"| Simple/basic offence punishment | {self._table_punishment(ipc_sources)} | {self._table_punishment(bns_sources)} |"
        )
        lines.append(
            f"| Repeat/aggravated offence punishment | {self._table_aggravated(ipc_sources)} | {self._table_aggravated(bns_sources)} |"
        )
        lines.append(
            f"| Cognisable status | {self._table_status(ipc_sources)} | {self._table_status(bns_sources)} |"
        )

        lines.extend(["", "STATUTORY SOURCES", ""])
        for source in sources:
            lines.append(
                f"[§{source['number']}]  {source['title']} Section {source['section']} {source['act']}"
            )
            lines.append(f"        Document type: {source['document_type']}")
            lines.append(
                f"        Chunk: {source['chunk']} of {source['total_chunks']}"
            )
            lines.append(f"        Similarity: {source['similarity']:.2f} score")
            lines.append(f'        Excerpt: "{source["excerpt"]}"')
            lines.append("")

        confidence = self._answer_confidence(sources)
        confidence_line = f"Answer confidence: {confidence}%"
        if sources[0]["similarity"] < 0.70:
            confidence_line += (
                " Low confidence — retrieved sources may not fully cover this query."
            )
        lines.append(confidence_line)
        lines.append("")
        lines.append(
            "Note: This information is provided for research purposes and does not constitute formal legal advice."
        )
        return "\n".join(lines)

    def _source_payload(self, item: dict, number: int, total_chunks: int) -> dict:
        metadata = item.get("metadata", {}) or {}
        citation = item.get("citation", {}) or {}
        document = " ".join((item.get("document") or "").split())
        act = (
            item.get("act") or metadata.get("act_name") or metadata.get("act") or ""
        ).upper() or "LEGAL"
        section = (
            citation.get("section") or metadata.get("section_number") or "unidentified"
        )
        title = metadata.get("source") or "Retrieved legal source"
        score = self._normalize_score(
            float(item.get("similarity_score", item.get("score", 0.0)) or 0.0)
        )

        return {
            "number": number,
            "title": title,
            "source_id": item.get("id"),
            "act": act,
            "section": section,
            "document_type": self._document_type(metadata),
            "chunk": int(metadata.get("chunk_index", number - 1) or 0) + 1,
            "total_chunks": total_chunks,
            "similarity": score,
            "excerpt": self._best_excerpt(document),
            "document": document,
            "reasons": item.get("reasons") or [],
        }

    def _best_source(self, sources: list[dict]) -> dict:
        return max(sources, key=lambda source: source["similarity"])

    def _normalize_score(self, score: float) -> float:
        if score <= 0:
            return 0.0
        if score <= 1:
            return score
        return 1.0

    def _document_type(self, metadata: dict) -> str:
        structure_type = str(metadata.get("structure_type", "")).lower()
        source = str(metadata.get("source", "")).lower()
        if "case" in structure_type or "judgment" in source:
            return "Case law"
        if "regulation" in structure_type:
            return "Regulation"
        if (
            "commentary" in structure_type
            or "textbook" in source
            or "ratanlal" in source
        ):
            return "Legal commentary"
        return "Statute"

    def _best_excerpt(self, document: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", document)
        keywords = (
            "punish",
            "imprison",
            "fine",
            "theft",
            "section",
            "cognizable",
            "cognisable",
            "community service",
        )
        for sentence in sentences:
            if "punishment for theft" in sentence.lower():
                excerpt = sentence.strip()
                words = excerpt.split()
                if len(words) > 40:
                    excerpt = " ".join(words[:40]).rstrip(",;:") + "..."
                return excerpt.replace('"', "'")

        ranked = sorted(
            (sentence.strip() for sentence in sentences if sentence.strip()),
            key=lambda sentence: sum(
                keyword in sentence.lower() for keyword in keywords
            ),
            reverse=True,
        )
        excerpt = ranked[0] if ranked else document[:220]
        words = excerpt.split()
        if len(words) > 40:
            excerpt = " ".join(words[:40]).rstrip(",;:") + "..."
        return excerpt.replace('"', "'")

    def _framework_sentence(self, source: dict) -> str:
        excerpt = source["excerpt"].rstrip(".")
        return f'Section {source["section"]} {source["act"]} is the retrieved provision; the source states: "{excerpt}."'

    def _table_section(self, sources: list[dict], act: str) -> str:
        if not sources:
            return "No direct source retrieved"
        source = self._best_source(sources)
        return f"Section {source['section']} {act} [§{source['number']}]"

    def _table_punishment(self, sources: list[dict]) -> str:
        source = self._first_matching_source(
            sources, ("punish", "imprison", "fine", "community service")
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _table_aggravated(self, sources: list[dict]) -> str:
        source = self._first_matching_source(
            sources, ("subsequent", "repeat", "aggravated", "second", "again")
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _table_status(self, sources: list[dict]) -> str:
        source = self._first_matching_source(
            sources, ("cognizable", "cognisable", "bailable", "non-cognizable")
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _first_matching_source(
        self, sources: list[dict], keywords: tuple[str, ...]
    ) -> dict | None:
        for source in sources:
            haystack = source["document"].lower()
            if any(keyword in haystack for keyword in keywords):
                return source
        return sources[0] if sources else None

    def _answer_confidence(self, sources: list[dict]) -> int:
        weighted_total = 0.0
        weight_sum = 0.0
        for index, source in enumerate(sources[:5], start=1):
            weight = 1.0 / index
            weighted_total += source["similarity"] * weight
            weight_sum += weight
        return round((weighted_total / max(weight_sum, 1e-9)) * 100)

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
                lines.append(
                    f"**Section:** {section}"
                    + (f" - {section_title}" if section_title else "")
                )
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
