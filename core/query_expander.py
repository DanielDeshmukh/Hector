"""
HECTOR Query Expander

Expands legal queries with synonyms and related terms before search.
Improves recall by matching more relevant documents.

Pipeline:
1. Detects legal terms in the query
2. Expands with synonyms and related concepts
3. Deduplicates to avoid redundant tokens
4. Returns expanded query string

Example:
    "bail" → "bail anticipatory bail default bail regular bail"
    "murder" → "murder culpable homicide section 302 culpable homicide not amounting to murder"
"""

import json
import logging
import os
import re
from typing import Dict, List

logger = logging.getLogger("hector.query_expander")

# Try loading auto-generated synonyms from corpus; fall back to built-in
_AUTO_SYNONYM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "auto_synonyms.json"
)


def _load_synonyms() -> Dict[str, List[str]]:
    """Load synonym dictionary, preferring corpus-generated file."""
    if os.path.exists(_AUTO_SYNONYM_PATH):
        try:
            with open(_AUTO_SYNONYM_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} auto-synonym groups from {_AUTO_SYNONYM_PATH}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load auto-synonyms: {e}, using built-in")

    # Fallback: built-in synonyms
    return {
        "murder": [
            "culpable homicide",
            "section 302",
            "section 101 bns",
            "homicide",
            "killing",
            "culpable homicide not amounting to murder",
            "section 304",
        ],
        "theft": [
            "larceny",
            "section 378",
            "section 303 bns",
            "stealing",
            "misappropriation",
            "dishonest taking",
        ],
        "robbery": [
            "dacoity",
            "section 392",
            "section 309 bns",
            "armed robbery",
            "theft with force",
        ],
        "fraud": [
            "cheating",
            "section 420",
            "section 318 bns",
            "deception",
            "forgery",
            "dishonesty",
        ],
        "assault": [
            "section 351",
            "section 115 bns",
            "battery",
            "hurt",
            "grievous hurt",
            "section 323",
            "section 124 bns",
        ],
        "rape": [
            "section 376",
            "sexual assault",
            "section 63 bns",
            "sexual intercourse without consent",
        ],
        "dowry": [
            "section 498a",
            "dowry death",
            "cruelty by husband",
            "dowry prohibition",
            "section 80 bns",
        ],
        "defamation": [
            "section 499",
            "section 356 bns",
            "libel",
            "slander",
            "good faith",
        ],
        "extortion": [
            "section 384",
            "section 308 bns",
            "blackmail",
            "coercion",
        ],
        "kidnapping": [
            "section 359",
            "section 137 bns",
            "abduction",
            "section 362",
        ],
        "criminal intimidation": [
            "section 506",
            "threat",
            "section 351 bns",
            "intimidation",
        ],
        "bail": [
            "anticipatory bail",
            "default bail",
            "regular bail",
            "interim bail",
            "section 437",
            "section 438",
            "section 480 bnss",
            "release on bail",
        ],
        "anticipatory bail": [
            "pre-arrest bail",
            "section 438 crpc",
            "section 482 bnss",
            "before arrest",
        ],
        "fir": [
            "first information report",
            "section 154 crpc",
            "section 173 bnss",
            "police complaint",
            "register fir",
        ],
        "charge sheet": [
            "chargesheet",
            "police report",
            "section 173 crpc",
            "final report",
            "section 193 bnss",
        ],
        "trial": [
            "hearing",
            "court proceedings",
            "examination",
            "cross-examination",
        ],
        "appeal": [
            "appellate",
            "section 374 crpc",
            "section 413 bnss",
            "higher court",
        ],
        "divorce": [
            "dissolution of marriage",
            "section 13 hindu marriage act",
            "irretrievable breakdown",
            "mutual consent divorce",
        ],
        "maintenance": [
            "alimony",
            "spousal support",
            "section 125 crpc",
            "section 144 bnss",
        ],
        "injunction": [
            "stay order",
            "temporary injunction",
            "order 39 cpc",
            "restraining order",
        ],
        "specific performance": [
            "section 10 specific relief act",
            "enforcement of contract",
            "compel performance",
        ],
        "damages": [
            "compensation",
            "monetary relief",
            "section 73 indian contract act",
            "loss of profit",
        ],
        "mortgage": [
            "home loan",
            "security interest",
            "section 58 transfer of property act",
            "pledge",
        ],
        "lease": [
            "rental agreement",
            "tenant",
            "landlord",
            "eviction",
            "section 105 transfer of property act",
        ],
        "partition": [
            "division of property",
            "coparcenary",
            "section 4 hindu succession act",
            "co-ownership",
        ],
        "fundamental rights": [
            "article 14",
            "article 19",
            "article 21",
            "part iii constitution",
            "right to equality",
            "right to life",
        ],
        "writ": [
            "habeas corpus",
            "mandamus",
            "certiorari",
            "quo warranto",
            "prohibition",
        ],
        "consumer complaint": [
            "deficiency in service",
            "defective goods",
            "section 34 consumer protection act",
            "consumer forum",
        ],
        "electronic evidence": [
            "section 65b",
            "digital evidence",
            "section 63 bharatiya sakshya",
            "computer output",
        ],
        "confession": [
            "admission",
            "section 25 evidence act",
            "section 22 bharatiya sakshya",
            "dying declaration",
        ],
        "unfair labour": [
            "industrial dispute",
            "section 2a industrial disputes act",
            "strike",
            "lockout",
            "retrenchment",
        ],
        "limitation": [
            "time bar",
            "limitation act",
            "section 3 limitation act",
            "prescription",
            "filing deadline",
        ],
        "minor": [
            "infant",
            "section 11 indian contract act",
            "capacity to contract",
            "guardian",
            "void agreement",
            "agreement by minor",
        ],
        "contract": [
            "agreement",
            "section 10 indian contract act",
            "void contract",
            "voidable contract",
            "breach of contract",
            "valid contract",
            "enforceable agreement",
        ],
        "inheritance": [
            "succession",
            "intestate",
            "hindu succession act",
            "heir",
            "coparcenary",
            "partition",
            "will",
            "testament",
            "probate",
        ],
        "wages": [
            "salary",
            "compensation",
            "minimum wages",
            "industrial disputes act",
            "payment of wages",
            "unpaid wages",
            "labour court",
        ],
        "drunk driving": [
            "dui",
            "driving under influence",
            "section 185 motor vehicles act",
            "intoxicated driving",
            "alcohol limit",
        ],
        "admissibility": [
            "evidence",
            "section 65b",
            "section 5 indian evidence act",
            "relevant facts",
            "proof",
        ],
        "interrogation": [
            "questioning",
            "police custody",
            "section 41 bnss",
            "section 41 crpc",
            "rights of accused",
            "legal counsel",
            "right to lawyer",
        ],
    }


class QueryExpander:
    """
    Expands legal queries with synonyms and related terms.
    Uses a curated legal dictionary for Indian law.
    """

    def __init__(self):
        self._synonyms = _load_synonyms()
        self._max_expansion_tokens = 50  # Max tokens to add

    def _find_matching_terms(self, query: str) -> List[str]:
        """Find all dictionary terms present in the query."""
        query_lower = query.lower()
        matched = []

        for term in self._synonyms:
            # Use word boundary matching for short terms, substring for phrases
            if len(term) <= 3:
                pattern = rf"\b{re.escape(term)}\b"
                if re.search(pattern, query_lower):
                    matched.append(term)
            else:
                if term in query_lower:
                    matched.append(term)

        return matched

    def _get_synonyms(self, terms: List[str]) -> List[str]:
        """Get synonyms for matched terms, deduplicated."""
        seen = set(terms)  # Don't repeat original terms
        synonyms = []

        for term in terms:
            for syn in self._synonyms.get(term, []):
                syn_lower = syn.lower()
                if syn_lower not in seen:
                    seen.add(syn_lower)
                    synonyms.append(syn)

        return synonyms

    def expand(self, query: str) -> str:
        """
        Expand a query with legal synonyms.

        Args:
            query: Original user query

        Returns:
            Expanded query with synonyms appended
        """
        matched_terms = self._find_matching_terms(query)

        if not matched_terms:
            return query

        synonyms = self._get_synonyms(matched_terms)

        if not synonyms:
            return query

        # Limit total expansion length
        expansion = " ".join(synonyms)
        expansion_words = expansion.split()

        if len(expansion_words) > self._max_expansion_tokens:
            expansion = " ".join(expansion_words[: self._max_expansion_tokens])

        expanded = f"{query} {expansion}"
        logger.debug(
            f"Expanded query: matched={matched_terms}, added={len(synonyms)} synonyms"
        )

        return expanded

    def expand_with_entities(self, query: str, entities: dict) -> str:
        """
        Expand query using both synonym dictionary and extracted entities.
        Entities come from the query parser (Phase A).
        """
        # Start with synonym expansion
        expanded = self.expand(query)

        # Add entity context if not already present
        query_lower = expanded.lower()

        # Add act names
        for act in entities.get("acts", []):
            if act.lower() not in query_lower:
                expanded += f" {act}"

        # Add section context
        for section in entities.get("sections", []):
            phrase = f"section {section}"
            if phrase not in query_lower:
                expanded += f" {phrase}"

        for section in entities.get("ipc_sections", []):
            phrase = f"section {section} ipc"
            if phrase not in query_lower:
                expanded += f" {phrase}"

        for section in entities.get("bns_sections", []):
            phrase = f"section {section} bns"
            if phrase not in query_lower:
                expanded += f" {phrase}"

        return expanded

    def get_synonyms(self, term: str) -> List[str]:
        """Get synonyms for a specific term (for debugging)."""
        return self._synonyms.get(term.lower(), [])

    def add_synonym_group(self, canonical: str, synonyms: List[str]):
        """Add a new synonym group at runtime."""
        if canonical in self._synonyms:
            self._synonyms[canonical].extend(synonyms)
        else:
            self._synonyms[canonical] = synonyms


# Singleton
_expander_instance = None


def get_query_expander() -> QueryExpander:
    """Get or create the singleton query expander."""
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = QueryExpander()
    return _expander_instance


def expand_query(query: str) -> str:
    """Convenience function to expand a query."""
    return get_query_expander().expand(query)
