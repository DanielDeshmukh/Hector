"""
Civil Law Module for HECTOR.
Handles civil law retrieval and CPC-specific queries.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


# Civil law acts to monitor
CIVIL_ACTS = [
    "Code of Civil Procedure",
    "CPC",
    "Civil Procedure Code",
    "Indian Contract Act",
    "Contract Act 1872",
    "Transfer of Property Act",
    "Property Act 1882",
    "Hindu Marriage Act",
    "Hindu Marriage Act 1955",
    "Hindu Succession Act",
    "Hindu Succession Act 1956",
    "Indian Succession Act",
    "Limitation Act",
    "Registration Act",
    "Specific Relief Act",
    "Trust Act",
    "Partition Act",
    "Easements Act",
]

# Civil law keywords for routing
CIVIL_KEYWORDS = (
    "cpc",
    "civil procedure",
    "code of civil procedure",
    "civil court",
    "district court",
    "high court civil",
    "civil suit",
    "plaint",
    "written statement",
    "written statement",
    "written statement",
    " decree",
    "execution",
    "limitation",
    "limitation act",
    "civil appeal",
    "civil revision",
    "civil misc",
    "cmc",
    "cmm",
    "small cause",
    "rent act",
    "tenancy",
    "eviction",
    "landlord",
    "tenant",
    "partition",
    "succession",
    "heir",
    "inheritance",
    "will",
    "probate",
    "letters of administration",
    "contract act",
    "agreement",
    "breach of contract",
    "specific performance",
    "indemnity",
    "guarantee",
    "bailment",
    "pledge",
    "agency",
    "partnership",
    "sale of goods",
    "conditional sale",
    "hire purchase",
    # Hindu law
    "hindu marriage",
    "hindu succession",
    "hindu adoption",
    "hindu minority",
    "maintenance",
    "alimony",
    "divorce",
    "judicial separation",
    "restitution",
    "dowry",
    "stridhan",
    # Property law
    "transfer of property",
    "sale deed",
    "gift deed",
    "mortgage",
    "lease",
    "license",
    "easement",
    "title",
    "conveyance",
    # General civil
    "injunction",
    "declaratory",
    "recovery",
    "money suit",
    "compensation",
    "damages",
    "specific relief",
    "res judicata",
    "collateral estoppel",
    "issue estoppel",
    "principle of merger",
)

# CPC-specific keywords
CPC_KEYWORDS = (
    "order 1",
    "order 2",
    "order 6",
    "order 7",
    "order 8",
    "order 9",
    "order 11",
    "order 12",
    "order 21",
    "order 22",
    "order 23",
    "order 32",
    "order 39",
    "order 47",
    "order 49",
    "rule 1",
    "rule 2",
    "schedule",
    "form",
    "appendix",
    "valuation",
    "jurisdiction",
    "place of suing",
    "institution of suit",
    "parties",
    "joinder",
    "misjoinder",
    "pleadings",
    "written statement",
    "replication",
    "amendment",
    "examination",
    "admission",
    "interrogatories",
    "discovery",
    "inspection",
    "production of documents",
    "commission",
    "interim application",
    "temporary injunction",
    "temporary relief",
    "appeal",
    "second appeal",
    " Letters Patent Appeal",
    "special appeal",
    "revision",
    "review",
    "review application",
    "caveat",
    "locus standi",
    "cause of action",
    "limitation period",
    "condonation of delay",
    "estoppel",
    "waiver",
    "res judicata",
    "constructive res judicata",
    "federal抵触",
    "cross-examination",
    "evidence",
    "documentary evidence",
    "oral evidence",
    "burden of proof",
    "presumption",
    "fiction of law",
    "document",
    "plaint",
    "written statement",
    "memo of parties",
    "title",
    "valuation",
    "court fee",
    "process fee",
    "summons",
    "service of summons",
    "substituted service",
    "efflux of time",
    "ex parte",
    "default judgment",
    "decree",
    "decree holder",
    "judgment debtor",
    "execution",
    "execution application",
    "attachment",
    "sale",
    "delivery",
    "mesne profit",
    "accounting",
    "appointment of receiver",
    "temporary injunction",
    "permanent injunction",
    "mandatory injunction",
    "prohibitory injunction",
    "declaration",
    "cancellation",
    "specific performance",
    "rescission",
    "reformation",
    "rectification",
)


@dataclass
class CivilLawAct:
    """Represents a civil law act with metadata."""
    name: str
    short_name: str
    year: int
    effective_date: str | None
    sections_count: int
    is_civil: bool = True


# Civil law acts catalog
CIVIL_LAW_ACTS = {
    "cpc": CivilLawAct(
        name="Code of Civil Procedure, 1908",
        short_name="CPC",
        year=1908,
        effective_date="01-01-1909",
        sections_count=158,
    ),
    "contract": CivilLawAct(
        name="Indian Contract Act, 1872",
        short_name="ICA",
        year=1872,
        effective_date="01-09-1872",
        sections_count=238,
    ),
    "transfer": CivilLawAct(
        name="Transfer of Property Act, 1882",
        short_name="TPA",
        year=1882,
        effective_date="01-07-1882",
        sections_count=137,
    ),
    "hindu_marriage": CivilLawAct(
        name="Hindu Marriage Act, 1955",
        short_name="HMA",
        year=1955,
        effective_date="18-05-1955",
        sections_count=37,
    ),
    "hindu_succession": CivilLawAct(
        name="Hindu Succession Act, 1956",
        short_name="HSA",
        year=1956,
        effective_date="17-06-1956",
        sections_count=40,
    ),
    "specific_relief": CivilLawAct(
        name="Specific Relief Act, 1963",
        short_name="SRA",
        year=1963,
        effective_date="01-07-1964",
        sections_count=22,
    ),
    "limitation": CivilLawAct(
        name="Limitation Act, 1963",
        short_name="LA",
        year=1963,
        effective_date="01-01-1964",
        sections_count=35,
    ),
    "registration": CivilLawAct(
        name="Indian Registration Act, 1908",
        short_name="RA",
        year=1908,
        effective_date="01-01-1909",
        sections_count=82,
    ),
}


class CivilLawRouter:
    """Routes civil law queries to appropriate handlers."""

    def __init__(self):
        self.civil_keywords = CIVIL_KEYWORDS
        self.cpc_keywords = CPC_KEYWORDS
        self.civil_acts = CIVIL_ACTS

    def is_civil_query(self, query: str) -> bool:
        """Check if query is about civil law."""
        lowered = query.lower()
        return any(kw in lowered for kw in self.civil_keywords)

    def is_cpc_query(self, query: str) -> bool:
        """Check if query is specifically about CPC."""
        lowered = query.lower()
        return any(kw in lowered for kw in self.cpc_keywords)

    def detect_civil_act(self, query: str) -> str | None:
        """Detect which civil act the query relates to."""
        lowered = query.lower()
        for act_name in self.civil_acts:
            if act_name.lower() in lowered:
                return act_name
        return None

    def route_civil_query(self, query: str) -> dict:
        """Route a civil law query to appropriate sub-route."""
        if self.is_cpc_query(query):
            return {
                "route": "CIVIL_PROCEDURE",
                "sub_route": "CPC",
                "confidence": 0.92,
            }

        act = self.detect_civil_act(query)
        if act:
            return {
                "route": "CIVIL_RESEARCH",
                "sub_route": act,
                "confidence": 0.89,
            }

        return {
            "route": "CIVIL_RESEARCH",
            "sub_route": "GENERAL_CIVIL",
            "confidence": 0.75,
        }


class CivilLawRetriever:
    """Retrieves civil law content with CPC-specific handling."""

    def __init__(self, retriever: "HectorHybridRetriever"):
        self.retriever = retriever
        self.router = CivilLawRouter()

    def search_civil_law(
        self,
        query: str,
        top_k: int = 10,
        filter_act: str | None = None,
    ) -> list[dict]:
        """
        Search for civil law content.

        Args:
            query: The search query
            top_k: Number of results to return
            filter_act: Optional filter for specific act

        Returns:
            List of search results
        """
        # Check if it's a CPC-specific query
        if self.router.is_cpc_query(query):
            # Add CPC context to query
            enhanced_query = f"CPC {query}"
            results = self.retriever.search(enhanced_query, top_k=top_k)

            # Also search for specific order/rule numbers
            order_match = query.lower()
            if "order" in order_match:
                # Extract order number and search specifically
                import re
                match = re.search(r'order\s+(\d+)', order_match)
                if match:
                    order_num = match.group(1)
                    order_results = self.retriever.search(
                        f"Order {order_num} CPC civil procedure",
                        top_k=top_k // 2,
                    )
                    results.extend(order_results)

            return results

        # General civil law search
        if filter_act:
            query = f"{filter_act} {query}"

        return self.retriever.search(query, top_k=top_k)

    def search_with_act_priority(
        self,
        query: str,
        acts: list[str],
        top_k: int = 10,
    ) -> list[dict]:
        """
        Search with prioritized acts.
        Higher priority acts appear first in results.
        """
        all_results = []

        for act in acts:
            act_results = self.retriever.search(f"{act} {query}", top_k=top_k)
            # Add act metadata for ranking
            for r in act_results:
                r["metadata"] = r.get("metadata", {})
                r["metadata"]["act_priority"] = acts.index(act)
            all_results.extend(act_results)

        # Sort by priority
        all_results.sort(key=lambda x: x.get("metadata", {}).get("act_priority", 999))

        return all_results[:top_k]

    def format_cpc_result(self, result: dict) -> str:
        """Format a CPC-specific result with order/rule context."""
        doc = result.get("document", "")
        metadata = result.get("metadata", {}) or {}

        section = metadata.get("section_number", "")
        chapter = metadata.get("chapter", "")
        order = metadata.get("order", "")
        rule = metadata.get("rule", "")

        formatted = []
        if order:
            formatted.append(f"Order {order} CPC")
        if rule:
            formatted.append(f"Rule {rule} CPC")
        if section:
            formatted.append(f"Section {section}")

        if chapter:
            formatted.append(f"- Chapter: {chapter}")

        if formatted:
            return f"[{' | '.join(formatted)}]\n\n{doc}"

        return doc


def get_civil_law_act_info(act_key: str) -> CivilLawAct | None:
    """Get information about a specific civil law act."""
    return CIVIL_LAW_ACTS.get(act_key)


def format_cpc_citation(section: str, order: str | None = None, rule: str | None = None) -> str:
    """Format a CPC citation properly."""
    parts = []
    if order:
        parts.append(f"Order {order}")
    if section:
        parts.append(f"Section {section}")
    if rule:
        parts.append(f"Rule {rule}")
    parts.append("CPC")
    return " | ".join(parts)