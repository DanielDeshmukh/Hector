"""
Judgment Precedent Analysis Module for HECTOR.
Handles case law citation and precedent tracking.
"""

from __future__ import annotations
import logging
import re
import httpx
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


# Case citation patterns
CITATION_PATTERNS = [
    r"\bAIR\s+\d{4}\s+[A-Z]+\s+\d+\b",  # AIR 2023 SC 123
    r"\bSCALE\s+\d{4}\s+[A-Z]+\s+\d+\b",  # SCALE 2023 123
    r"\bSCC\s+\d{4}\s+[A-Z]+\s+\d+\b",  # SCC 2023 123
    r"\b\(\d{4}\)\s*\d+\s*SC[RT]?\b",  # (2023) 1 SCR 123
    r"\b\d{1,2}\s*SCC\s*\(\d{4}\)\b",  # 12 SCC (2023)
    r"\bILR\s+\d{4}\s+[A-Z]+\s+\d+\b",  # ILR 2023 Del 123
    r"\b\(?\(\d{4}\)\s*\(?\d+\)?\s*CLT\b",  # (2023) 1 CLT
]

# Courts registry
COURTS = {
    "supreme_court": {
        "name": "Supreme Court of India",
        "short": "SC",
        "website": "sci.gov.in",
        "benches": ["Chief Justice", "Full Bench", "Division Bench", "Single Judge"],
    },
    "delhi_high_court": {
        "name": "Delhi High Court",
        "short": "DelHC",
        "website": "delhihighcourt.nic.in",
    },
    "bombay_high_court": {
        "name": "Bombay High Court",
        "short": "BomHC",
        "website": "bombayhighcourt.nic.in",
    },
    "madras_high_court": {
        "name": "Madras High Court",
        "short": "MadHC",
        "website": "madrashighcourt.nic.in",
    },
    "calcutta_high_court": {
        "name": "Calcutta High Court",
        "short": "CalHC",
        "website": "calcuttahighcourt.nic.in",
    },
}


@dataclass
class Judge:
    """Represents a judge in a bench."""
    name: str
    role: str  # Chief Justice, Senior Judge, Judge
    tenure_start: int | None = None
    tenure_end: int | None = None


@dataclass
class CaseCitation:
    """Represents a case citation within a judgment."""
    case_name: str
    citation: str
    year: int | None
    court: str
    is_cited_by: list[str] = field(default_factory=list)
    cites: list[str] = field(default_factory=list)
    followed_in: list[str] = field(default_factory=list)
    overruled_in: list[str] = field(default_factory=list)


@dataclass
class Precedent:
    """Represents a legal precedent with analysis."""
    case_id: str
    case_name: str
    citation: str
    court: str
    bench_size: int
    judges: list[Judge]
    date: datetime | None
    ratio_decidendi: str | None = None
    cited_by: list[str] = field(default_factory=list)
    cites: list[str] = field(default_factory=list)
    followed_in: list[str] = field(default_factory=list)
    overruled_in: list[str] = field(default_factory=list)
    status: str = "active"  # active, overruled, modified, followed
    precedent_strength: float = 0.5  # 0-1 scale
    keywords: list[str] = field(default_factory=list)


class PrecedentAnalyzer:
    """Analyzes case law and creates precedent networks."""

    def __init__(self, retriever: "HectorHybridRetriever | None" = None):
        self.retriever = retriever
        self.precedent_index: dict[str, Precedent] = {}
        self.citation_graph: dict[str, list[str]] = {}  # case_id -> cited_cases

    def add_case(
        self,
        case_id: str,
        case_name: str,
        citation: str,
        court: str,
        bench: list[Judge],
        date: datetime | None = None,
        ratio: str | None = None,
    ) -> Precedent:
        """Add a case to the precedent index."""
        precedent = Precedent(
            case_id=case_id,
            case_name=case_name,
            citation=citation,
            court=court,
            bench_size=len(bench),
            judges=bench,
            date=date,
            ratio_decidendi=ratio,
            status="active",
            precedent_strength=self._calculate_strength(len(bench), court),
        )

        self.precedent_index[case_id] = precedent

        # Build citation graph
        if case_id not in self.citation_graph:
            self.citation_graph[case_id] = []

        return precedent

    def _calculate_strength(self, bench_size: int, court: str) -> float:
        """Calculate precedent strength based on bench and court."""
        # Full bench > Division bench > Single judge
        bench_factor = min(bench_size / 5, 1.0) * 0.3

        # Supreme Court > High Court
        court_factor = 0.5 if court == "supreme_court" else 0.2

        return min(bench_factor + court_factor + 0.2, 1.0)

    def add_citation(self, from_case: str, to_case: str) -> None:
        """Add a citation relationship between cases."""
        if from_case not in self.citation_graph:
            self.citation_graph[from_case] = []

        if to_case not in self.citation_graph[from_case]:
            self.citation_graph[from_case].append(to_case)

        # Update cited_by on target
        if to_case in self.precedent_index:
            if from_case not in self.precedent_index[to_case].cited_by:
                self.precedent_index[to_case].cited_by.append(from_case)

        # Update cites on source
        if from_case in self.precedent_index:
            if to_case not in self.precedent_index[from_case].cites:
                self.precedent_index[from_case].cites.append(to_case)

    def mark_overruled(self, case_id: str, overruled_by: str) -> None:
        """Mark a case as overruled by another case."""
        if case_id in self.precedent_index:
            self.precedent_index[case_id].status = "overruled"
            self.precedent_index[case_id].precedent_strength = 0.1

        # Update overruled_by reference
        if overruled_by in self.precedent_index:
            if case_id not in self.precedent_index[overruled_by].overruled_in:
                self.precedent_index[overruled_by].overruled_in.append(case_id)

    def mark_followed(self, case_id: str, followed_by: str) -> None:
        """Mark a case as followed by another case."""
        if case_id in self.precedent_index:
            if followed_by not in self.precedent_index[case_id].followed_in:
                self.precedent_index[case_id].followed_in.append(followed_by)

    def get_cited_cases(self, case_id: str) -> list[Precedent]:
        """Get all cases cited by this case."""
        if case_id not in self.citation_graph:
            return []

        return [
            self.precedent_index[c]
            for c in self.citation_graph[case_id]
            if c in self.precedent_index
        ]

    def get_citing_cases(self, case_id: str) -> list[Precedent]:
        """Get all cases that cite this case."""
        if case_id not in self.precedent_index:
            return []

        return [
            self.precedent_index[c]
            for c in self.precedent_index[case_id].cited_by
            if c in self.precedent_index
        ]

    def get_related_precedents(
        self,
        case_id: str,
        max_distance: int = 2,
    ) -> list[Precedent]:
        """Get related precedents within N degrees of separation."""
        if case_id not in self.precedent_index:
            return []

        related = set()
        queue = [(case_id, 0)]
        visited = {case_id}

        while queue:
            current, distance = queue.pop(0)
            if distance >= max_distance:
                continue

            # Get cases this case cites
            for cited in self.citation_graph.get(current, []):
                if cited not in visited:
                    visited.add(cited)
                    related.add(cited)
                    queue.append((cited, distance + 1))

            # Get cases that cite this case
            for citing in self.precedent_index[current].cited_by:
                if citing not in visited:
                    visited.add(citing)
                    related.add(citing)
                    queue.append((citing, distance + 1))

        return [self.precedent_index[c] for c in related if c in self.precedent_index]

    def extract_ratio_decidendi(self, case_text: str) -> str | None:
        """Extract ratio decidendi from case text."""
        # Common patterns for ratio extraction
        patterns = [
            r"(?i)the\s+principle\s+laid\s+down\s+is[:\s]+(.+?)(?:\n\n|\.\s)",
            r"(?i)the\s+law\s+laid\s+down\s+is[:\s]+(.+?)(?:\n\n|\.\s)",
            r"(?i)holding\s+that[:\s]+(.+?)(?:\n\n|\.\s)",
            r"(?i)it\s+is\s+well\s+settled\s+that[:\s]+(.+?)(?:\n\n|\.\s)",
            r"(?i)the\s+ratio\s+decidendi\s+is[:\s]+(.+?)(?:\n\n|\.\s)",
        ]

        for pattern in patterns:
            match = re.search(pattern, case_text, re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # Limit length

        return None

    def search_by_citation(self, citation: str) -> Precedent | None:
        """Search for a case by its citation."""
        for precedent in self.precedent_index.values():
            if citation.lower() in precedent.citation.lower():
                return precedent
        return None

    def search_by_keyword(self, keyword: str) -> list[Precedent]:
        """Search precedents by keyword."""
        keyword_lower = keyword.lower()
        results = []

        for precedent in self.precedent_index.values():
            if keyword_lower in precedent.case_name.lower():
                results.append(precedent)
            elif any(keyword_lower in k.lower() for k in precedent.keywords):
                results.append(precedent)
            elif precedent.ratio_decidendi and keyword_lower in precedent.ratio_decidendi.lower():
                results.append(precedent)

        # Sort by strength
        results.sort(key=lambda x: x.precedent_strength, reverse=True)
        return results

    def get_precedent_chain(
        self,
        case_id: str,
        direction: str = "both",
    ) -> list[Precedent]:
        """Get the full precedent chain for a case."""
        if case_id not in self.precedent_index:
            return []

        chain = []

        if direction in ("both", "backward"):
            # Get cases this case relies on
            chain.extend(self._get_citation_chain(case_id, "cites"))

        if direction in ("both", "forward"):
            # Get cases that rely on this case
            chain.extend(self._get_citation_chain(case_id, "cited_by"))

        # Sort by date
        chain.sort(key=lambda x: x.date or datetime.min, reverse=True)
        return chain

    def _get_citation_chain(self, case_id: str, relation: str) -> list[Precedent]:
        """Helper to get citation chain."""
        if case_id not in self.precedent_index:
            return []

        if relation == "cites":
            case_ids = self.precedent_index[case_id].cites
        else:
            case_ids = self.precedent_index[case_id].cited_by

        return [
            self.precedent_index[c]
            for c in case_ids
            if c in self.precedent_index
        ]

    def get_statistics(self) -> dict:
        """Get statistics about the precedent index."""
        total = len(self.precedent_index)
        overruled = sum(1 for p in self.precedent_index.values() if p.status == "overruled")
        followed = sum(1 for p in self.precedent_index.values() if p.followed_in)
        avg_strength = sum(p.precedent_strength for p in self.precedent_index.values()) / max(total, 1)

        return {
            "total_cases": total,
            "overruled_cases": overruled,
            "followed_cases": followed,
            "average_strength": round(avg_strength, 2),
            "total_citations": sum(len(v.cites) for v in self.precedent_index.values()),
        }


class JudgmentScraper:
    """Scraper for fetching judgments from court websites."""

    # Court base URLs
    SC_BASE_URL = "https://main.sci.gov.in"
    HIGH_COURT_BASE = "https://"

    def __init__(self):
        self.courts = COURTS

    async def fetch_supreme_courtJudgment(self, case_no: str) -> dict | None:
        """Fetch a Supreme Court judgment from the main SCI website."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.SC_BASE_URL}/judgments"
                response = await client.get(
                    url,
                    params={"caseNo": case_no},
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                html = response.text

                # Extract judgment text
                text_match = re.search(
                    r'<div[^>]*class="[^"]*judgment[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                judgment_text = text_match.group(1).strip() if text_match else ""
                # Clean HTML tags from text
                judgment_text = re.sub(r"<[^>]+>", " ", judgment_text).strip()

                # Extract date
                date_match = re.search(
                    r'<span[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</span>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                date_str = date_match.group(1).strip() if date_match else ""

                # Extract bench
                bench_match = re.search(
                    r'<div[^>]*class="[^"]*bench[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                bench = bench_match.group(1).strip() if bench_match else ""

                # Extract parties
                parties_match = re.search(
                    r'<div[^>]*class="[^"]*parties[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                parties = parties_match.group(1).strip() if parties_match else ""
                # Clean HTML from parties
                parties = re.sub(r"<[^>]+>", " ", parties).strip()

                return {
                    "case_no": case_no,
                    "court": "supreme_court",
                    "date": date_str,
                    "bench": bench,
                    "parties": parties,
                    "text": judgment_text,
                    "base_url": self.SC_BASE_URL,
                    "status": "success",
                }
        except httpx.TimeoutException as e:
            logger.warning("Timeout fetching Supreme Court judgment for %s: %s", case_no, e)
            return {
                "case_no": case_no,
                "court": "supreme_court",
                "base_url": self.SC_BASE_URL,
                "status": "error",
                "error": str(e),
            }
        except httpx.HTTPError as e:
            logger.warning("HTTP error fetching Supreme Court judgment for %s: %s", case_no, e)
            return {
                "case_no": case_no,
                "court": "supreme_court",
                "base_url": self.SC_BASE_URL,
                "status": "error",
                "error": str(e),
            }
        except Exception as e:
            logger.warning("Error fetching Supreme Court judgment for %s: %s", case_no, e)
            return {
                "case_no": case_no,
                "court": "supreme_court",
                "base_url": self.SC_BASE_URL,
                "status": "error",
                "error": str(e),
            }

    async def fetch_high_court_judgment(self, court: str, case_no: str) -> dict | None:
        """Fetch a High Court judgment from the respective court website."""
        court_info = self.courts.get(court)
        if not court_info:
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                website = court_info["website"]
                url = f"https://{website}/judgments"
                response = await client.get(
                    url,
                    params={"caseNo": case_no},
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                html = response.text

                # Extract judgment text
                text_match = re.search(
                    r'<div[^>]*class="[^"]*judgment[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                judgment_text = text_match.group(1).strip() if text_match else ""
                # Clean HTML tags from text
                judgment_text = re.sub(r"<[^>]+>", " ", judgment_text).strip()

                # Extract date
                date_match = re.search(
                    r'<span[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</span>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                date_str = date_match.group(1).strip() if date_match else ""

                # Extract bench
                bench_match = re.search(
                    r'<div[^>]*class="[^"]*bench[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                bench = bench_match.group(1).strip() if bench_match else ""

                # Extract parties
                parties_match = re.search(
                    r'<div[^>]*class="[^"]*parties[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                parties = parties_match.group(1).strip() if parties_match else ""
                # Clean HTML from parties
                parties = re.sub(r"<[^>]+>", " ", parties).strip()

                return {
                    "case_no": case_no,
                    "court": court,
                    "date": date_str,
                    "bench": bench,
                    "parties": parties,
                    "text": judgment_text,
                    "base_url": f"https://{website}",
                    "status": "success",
                }
        except httpx.TimeoutException as e:
            logger.warning("Timeout fetching %s judgment for %s: %s", court, case_no, e)
            return {
                "case_no": case_no,
                "court": court,
                "base_url": f"https://{court_info['website']}",
                "status": "error",
                "error": str(e),
            }
        except httpx.HTTPError as e:
            logger.warning("HTTP error fetching %s judgment for %s: %s", court, case_no, e)
            return {
                "case_no": case_no,
                "court": court,
                "base_url": f"https://{court_info['website']}",
                "status": "error",
                "error": str(e),
            }
        except Exception as e:
            logger.warning("Error fetching %s judgment for %s: %s", court, case_no, e)
            return {
                "case_no": case_no,
                "court": court,
                "base_url": f"https://{court_info['website']}",
                "status": "error",
                "error": str(e),
            }

    def parse_citation(self, citation: str) -> dict | None:
        """Parse a citation string into components."""
        # Try to parse AIR citation
        air_match = re.match(r"AIR\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE)
        if air_match:
            return {
                "type": "AIR",
                "year": int(air_match.group(1)),
                "court": air_match.group(2),
                "case_no": int(air_match.group(3)),
            }

        # Try SCC
        scc_match = re.match(r"SCC\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE)
        if scc_match:
            return {
                "type": "SCC",
                "year": int(scc_match.group(1)),
                "court": scc_match.group(2),
                "case_no": int(scc_match.group(3)),
            }

        return None


def format_citation_with_status(precedent: Precedent) -> str:
    """Format a citation with its current status."""
    status_emoji = {
        "active": "✓",
        "overruled": "✗",
        "modified": "~",
        "followed": "★",
    }

    emoji = status_emoji.get(precedent.status, "?")

    parts = [f"{emoji} {precedent.citation}"]

    if precedent.followed_in:
        parts.append(f"(followed in {len(precedent.followed_in)} cases)")

    if precedent.status == "overruled":
        parts.append("(overruled)")

    return " ".join(parts)