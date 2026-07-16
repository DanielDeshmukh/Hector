"""
HECTOR Entity-Aware Re-ranker

Boosts search results that match extracted legal entities.
Sits on top of the hybrid retriever's existing reranking.

How it works:
1. Receives search results + extracted entities from query parser
2. Checks each result for entity matches (section, act, topic, article)
3. Applies a boost to the score for each match type
4. Re-ranks results by boosted score

Boost weights (configurable):
- Section number match: +0.15 (strongest signal)
- Act name match: +0.10
- Topic match: +0.05
- Article match: +0.10
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hector.entity_reranker")


class EntityReranker:
    """
    Re-ranks search results based on entity matches.
    Applies score boosts for results that contain extracted legal entities.
    """

    # Boost weights for different match types
    BOOST_WEIGHTS = {
        "section": 0.15,  # Section number in document
        "act": 0.10,  # Act name in document
        "topic": 0.05,  # Legal topic in document
        "article": 0.10,  # Constitutional article in document
        "citation": 0.08,  # Citation metadata match
    }

    def __init__(self, boost_weights: Optional[Dict[str, float]] = None):
        if boost_weights:
            self.BOOST_WEIGHTS = boost_weights

    def rerank(
        self,
        results: List[Dict[str, Any]],
        entities: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results based on entity matches.

        Args:
            results: Search results from hybrid retriever
            entities: Extracted entities from query parser (LegalEntities.to_dict())

        Returns:
            Re-ranked results with boosted scores
        """
        if not results or not entities:
            return results

        for item in results:
            boost = self._calculate_boost(item, entities)
            if boost > 0:
                # Apply boost to the existing score
                original_score = item.get("score", 0.0)
                boosted_score = min(1.0, original_score + boost)
                item["score"] = round(boosted_score, 6)
                item["entity_boost"] = round(boost, 6)

                # Track why it was boosted
                reasons = item.get("reasons", [])
                if boost >= 0.15:
                    reasons.append("entity-boost-strong")
                elif boost >= 0.10:
                    reasons.append("entity-boost-medium")
                else:
                    reasons.append("entity-boost-light")
                item["reasons"] = reasons

        # Re-sort by boosted score
        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results

    def _calculate_boost(self, item: Dict[str, Any], entities: Dict[str, Any]) -> float:
        """Calculate total boost for a single result."""
        boost = 0.0

        # Get document content and metadata
        doc_text = (item.get("document") or "").lower()
        metadata = item.get("metadata", {})
        source = (metadata.get("source") or "").lower()
        real_act = (
            metadata.get("real_act_name") or metadata.get("act_name") or ""
        ).lower()
        citation = item.get("citation", {})
        act_in_result = (item.get("act") or "").lower()

        # 1. Section number match
        section_boost = self._check_section_match(doc_text, citation, entities, metadata)
        boost += section_boost

        # 2. Act name match (prefer real_act_name over source filename)
        act_boost = self._check_act_match(
            doc_text, real_act or source, act_in_result, entities
        )
        boost += act_boost

        # 3. Topic match
        topic_boost = self._check_topic_match(doc_text, entities)
        boost += topic_boost

        # 4. Article match
        article_boost = self._check_article_match(doc_text, entities)
        boost += article_boost

        return boost

    def _check_section_match(
        self, doc_text: str, citation: Dict, entities: Dict, metadata: Dict = None
    ) -> float:
        """Check if the document matches an expected section number.

        Priority: metadata tag > citation > text substring.
        A chunk whose section_number metadata matches is much more likely
        to be ABOUT that section than one that merely mentions it.
        """
        boost = 0.0

        all_sections = (
            entities.get("sections", [])
            + entities.get("ipc_sections", [])
            + entities.get("bns_sections", [])
        )

        metadata_section = ""
        if metadata:
            metadata_section = str(metadata.get("section_number", "")).lower()

        for section in all_sections:
            section_lower = section.lower()

            # Strongest signal: metadata tag matches exactly
            if metadata_section and metadata_section == section_lower:
                boost = max(boost, 0.25)  # Higher than old 0.15
                break

            # Medium signal: citation metadata matches
            citation_section = (citation.get("section") or "").lower()
            if citation_section == section_lower:
                boost = max(boost, 0.15)
                break

            # Weakest signal: section mentioned in text
            patterns = [
                rf"section\s+{re.escape(section_lower)}",
                rf"s\.?\s*{re.escape(section_lower)}",
                rf"\[s\s*{re.escape(section_lower)}\]",
            ]
            for pattern in patterns:
                if re.search(pattern, doc_text):
                    boost = max(boost, 0.05)  # Reduced from 0.15
                    break

        return boost

    def _check_act_match(
        self, doc_text: str, source: str, act_in_result: str, entities: Dict
    ) -> float:
        """Check if the document matches an expected act."""
        boost = 0.0
        expected_acts = entities.get("acts", [])

        if not expected_acts:
            return 0.0

        # Normalize expected act names for comparison
        act_keywords = {
            "Indian Penal Code": ["ipc", "indian penal code", "penal code"],
            "Bharatiya Nyaya Sanhita": ["bns", "bharatiya nyaya"],
            "Code of Criminal Procedure": [
                "crpc",
                "code of criminal",
                "criminal procedure",
            ],
            "Bharatiya Nagarik Suraksha Sanhita": ["bnss", "bharatiya nagarik"],
            "Indian Evidence Act": ["evidence act", "indian evidence"],
            "Bharatiya Sakshya Adhiniyam": ["bharatiya sakshya", "sakshya adhiniyam"],
            "Code of Civil Procedure": ["cpc", "code of civil", "civil procedure"],
            "Transfer of Property Act": ["transfer of property"],
            "Indian Contract Act": ["contract act", "indian contract"],
            "Consumer Protection Act": ["consumer protection"],
            "NDPS Act": ["ndps", "narcotic drugs"],
            "Motor Vehicles Act": ["motor vehicles"],
            "Hindu Succession Act": ["hindu succession"],
            "Hindu Marriage Act": ["hindu marriage"],
            "Constitution of India": ["constitution", "constitutional"],
        }

        for expected_act in expected_acts:
            keywords = act_keywords.get(expected_act, [expected_act.lower()])

            for keyword in keywords:
                # Also replace underscores with spaces for source comparison
                source_normalized = source.replace("_", " ")
                if (
                    keyword in doc_text
                    or keyword in source_normalized
                    or keyword in source
                    or keyword in act_in_result
                ):
                    boost = max(boost, self.BOOST_WEIGHTS["act"])
                    break

            if boost > 0:
                break

        return boost

    def _check_topic_match(self, doc_text: str, entities: Dict) -> float:
        """Check if the document contains matching legal topics."""
        topics = entities.get("topics", [])
        if not topics:
            return 0.0

        # Simple keyword matching for topics
        topic_keywords = {
            "bail": ["bail", "anticipatory bail", "default bail"],
            "anticipatory_bail": [
                "anticipatory bail",
                "pre-arrest bail",
                "section 438",
            ],
            "murder": ["murder", "culpable homicide", "section 302"],
            "theft": ["theft", "larceny", "section 378"],
            "rape": ["rape", "sexual assault", "section 376"],
            "dowry": ["dowry", "cruelty", "section 498a"],
            "fraud": ["fraud", "cheating", "forgery"],
            "divorce": ["divorce", "dissolution", "section 13"],
            "fir": ["fir", "first information report", "section 154"],
        }

        for topic in topics:
            keywords = topic_keywords.get(topic, [topic.replace("_", " ")])
            for keyword in keywords:
                if keyword.lower() in doc_text:
                    return self.BOOST_WEIGHTS["topic"]

        return 0.0

    def _check_article_match(self, doc_text: str, entities: Dict) -> float:
        """Check if the document contains matching constitutional articles."""
        articles = entities.get("articles", [])
        if not articles:
            return 0.0

        for article in articles:
            # Check for "article 21" pattern
            pattern = rf"article\s+{re.escape(article.lower())}"
            if re.search(pattern, doc_text):
                return self.BOOST_WEIGHTS["article"]

        return 0.0


# Singleton
_reranker_instance = None


def get_entity_reranker() -> EntityReranker:
    """Get or create the singleton entity reranker."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = EntityReranker()
    return _reranker_instance


def rerank_by_entities(
    results: List[Dict[str, Any]], entities: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Convenience function to re-rank results by entity matches."""
    return get_entity_reranker().rerank(results, entities)
