"""
Tests for HECTOR Entity-Aware Re-ranker (Phase D)
Validates entity-based score boosting for search results.
Uses unittest (no pytest dependency).
"""

import unittest
from core.entity_reranker import EntityReranker, get_entity_reranker, rerank_by_entities


def make_result(doc, score=0.5, source="Unknown", act="", section=None):
    """Helper to create a search result dict."""
    result = {
        "document": doc,
        "score": score,
        "metadata": {"source": source, "page": 1},
        "reasons": [],
    }
    if act:
        result["act"] = act
    if section:
        result["citation"] = {"section": section}
    else:
        result["citation"] = {}
    return result


class TestSectionBoost(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_section_match_in_text(self):
        results = [make_result("Section 302 IPC murder punishment", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)
        self.assertIn("entity-boost-strong", reranked[0]["reasons"])

    def test_section_no_match(self):
        results = [make_result("Section 376 IPC rape punishment", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertEqual(reranked[0]["score"], 0.5)

    def test_section_match_in_citation(self):
        results = [make_result("Murder punishment", score=0.5, section="302")]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_ipc_section_match(self):
        results = [make_result("Section 302 IPC punishment", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": ["302"],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_bns_section_match(self):
        results = [make_result("Section 101 BNS culpable homicide", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": ["101"],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)


class TestActBoost(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_act_match_in_text(self):
        results = [make_result("Indian Penal Code Section 302 murder", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_act_match_in_source(self):
        results = [
            make_result("Section 302 murder", score=0.5, source="Indian_Penal_Code")
        ]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_act_match_in_act_field(self):
        results = [
            make_result("Section 302 murder", score=0.5, act="Indian Penal Code")
        ]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_no_act_match(self):
        results = [make_result("Consumer Protection Act complaint", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertEqual(reranked[0]["score"], 0.5)


class TestTopicBoost(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_topic_match(self):
        results = [make_result("Grant of bail conditions", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": ["bail"],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_no_topic_match(self):
        results = [make_result("Section 302 murder", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": ["divorce"],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertEqual(reranked[0]["score"], 0.5)


class TestArticleBoost(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_article_match(self):
        results = [
            make_result("Article 21 right to life and personal liberty", score=0.5)
        ]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": ["21"],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)

    def test_no_article_match(self):
        results = [make_result("Article 14 equality", score=0.5)]
        entities = {
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": ["21"],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertEqual(reranked[0]["score"], 0.5)


class TestReranking(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_higher_entity_score_comes_first(self):
        """Results with entity matches should rank higher."""
        results = [
            make_result("Consumer protection complaint", score=0.6),
            make_result("Section 302 IPC murder", score=0.5),
        ]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        # The second result (Section 302) should now be first
        self.assertIn("302", reranked[0]["document"])

    def test_score_capped_at_one(self):
        """Boosted score should not exceed 1.0."""
        results = [make_result("Section 302 IPC murder", score=0.95)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": ["murder"],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertLessEqual(reranked[0]["score"], 1.0)

    def test_multiple_boosts_accumulate(self):
        """Multiple entity matches should stack boosts."""
        results = [make_result("Section 302 IPC murder", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": ["murder"],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        # Section + Act + Topic = 0.15 + 0.10 + 0.05 = 0.30 boost
        self.assertAlmostEqual(reranked[0]["score"], 0.80, places=2)


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.reranker = EntityReranker()

    def test_empty_results(self):
        reranked = self.reranker.rerank([], {"sections": ["302"]})
        self.assertEqual(reranked, [])

    def test_no_entities(self):
        results = [make_result("Section 302 murder", score=0.5)]
        reranked = self.reranker.rerank(results, None)
        self.assertEqual(reranked[0]["score"], 0.5)

    def test_empty_entities(self):
        results = [make_result("Section 302 murder", score=0.5)]
        reranked = self.reranker.rerank(results, {})
        self.assertEqual(reranked[0]["score"], 0.5)

    def test_entity_boost_field_added(self):
        results = [make_result("Section 302 murder", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = self.reranker.rerank(results, entities)
        self.assertIn("entity_boost", reranked[0])
        self.assertGreater(reranked[0]["entity_boost"], 0)


class TestConvenienceFunctions(unittest.TestCase):
    def test_get_entity_reranker_singleton(self):
        r1 = get_entity_reranker()
        r2 = get_entity_reranker()
        self.assertIs(r1, r2)

    def test_rerank_by_entities(self):
        results = [make_result("Section 302 murder", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": [],
            "topics": [],
            "articles": [],
        }
        reranked = rerank_by_entities(results, entities)
        self.assertGreater(reranked[0]["score"], 0.5)


class TestCustomWeights(unittest.TestCase):
    def test_custom_boost_weights(self):
        custom_weights = {
            "section": 0.30,
            "act": 0.20,
            "topic": 0.10,
            "article": 0.20,
            "citation": 0.15,
        }
        reranker = EntityReranker(boost_weights=custom_weights)
        results = [make_result("Section 302 IPC murder", score=0.5)]
        entities = {
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
            "acts": ["Indian Penal Code"],
            "topics": ["murder"],
            "articles": [],
        }
        reranked = reranker.rerank(results, entities)
        # Section + Act + Topic = 0.30 + 0.20 + 0.10 = 0.60 boost
        self.assertAlmostEqual(reranked[0]["score"], 1.0, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
