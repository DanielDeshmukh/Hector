"""
Tests for HECTOR Query Expander (Phase C)
Validates legal synonym expansion for improved recall.
Uses unittest (no pytest dependency).
"""

import unittest
from core.query_expander import QueryExpander, get_query_expander, expand_query


class TestBasicExpansion(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_bail_expansion(self):
        result = self.expander.expand("bail")
        self.assertIn("anticipatory bail", result)
        self.assertIn("default bail", result)
        self.assertIn("regular bail", result)

    def test_murder_expansion(self):
        result = self.expander.expand("murder punishment")
        self.assertIn("culpable homicide", result)
        self.assertIn("section 302", result)

    def test_theft_expansion(self):
        result = self.expander.expand("theft")
        self.assertIn("section 378", result)
        self.assertIn("misappropriation", result)

    def test_fir_expansion(self):
        result = self.expander.expand("how to file FIR")
        self.assertIn("first information report", result)
        self.assertIn("section 154", result)

    def test_divorce_expansion(self):
        result = self.expander.expand("divorce")
        self.assertIn("dissolution of marriage", result)
        self.assertIn("hindu marriage act", result)


class TestNoExpansion(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_empty_query(self):
        result = self.expander.expand("")
        self.assertEqual(result, "")

    def test_irrelevant_query(self):
        result = self.expander.expand("What is the weather today?")
        self.assertEqual(result, "What is the weather today?")

    def test_preserves_original(self):
        original = "Section 302 IPC murder"
        result = self.expander.expand(original)
        self.assertIn(original, result)


class TestActNameReverseMatch(unittest.TestCase):
    """Naming an act must not fire every synonym group citing that act.

    Regression: _find_matching_terms reverse-matched values, and act titles
    are values shared by many groups ("Indian Penal Code" is a value in 24
    of the 81 auto-synonym groups). Any question naming an act but no crime
    keyword therefore appended ~50 tokens of foreign section numbers, which
    pushed the expected section out of the fusion pool (8 of the 9 residual
    misses in the 4-act retrieval gate, 2026-10-10).
    """

    def setUp(self):
        self.expander = QueryExpander()

    def test_act_name_alone_does_not_expand(self):
        q = "What are the provisions of the Indian Penal Code regarding number?"
        self.assertEqual(self.expander.expand(q), q)

    def test_act_name_reverse_match_fires_nothing(self):
        q = "What does the Bharatiya Nyaya Sanhita say about 255?"
        self.assertEqual(self.expander._find_matching_terms(q), [])

    def test_act_name_query_has_no_section_tail(self):
        q = "What treatment does the Indian Penal Code provide for person?"
        out = self.expander.expand(q)
        self.assertNotIn("section 113A", out)
        self.assertNotIn("section 107", out)
        self.assertNotIn("section 44", out)

    def test_bnss_act_name_query_stays_raw(self):
        q = ("Under the Bharatiya Nagarik Suraksha Sanhita, what applies to "
             "application of this chapter?")
        self.assertEqual(self.expander.expand(q), q)

    def test_statute_value_skip_keeps_topic_reverse_match(self):
        # "first information report" is a VALUE of key "fir"; forward matching
        # finds no key, so this only works through reverse value->key matching.
        self.assertIn("fir", self.expander._find_matching_terms(
            "first information report"))

    def test_topic_keyword_still_expands_in_act_query(self):
        out = self.expander.expand("murder under the Indian Penal Code")
        self.assertIn("culpable homicide", out)

    def test_explicit_section_query_still_untouched(self):
        q = "Section 302 IPC murder punishment"
        self.assertEqual(self.expander.expand(q), q)


class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_no_duplicate_original_terms(self):
        """Original query terms should not appear as standalone duplicates."""
        result = self.expander.expand("bail")
        # The word "bail" appears in compound synonyms like "anticipatory bail"
        # which is expected. Check that the original query is preserved exactly.
        self.assertTrue(result.startswith("bail"))

    def test_no_duplicate_synonyms(self):
        """Same synonym shouldn't appear twice."""
        result = self.expander.expand("bail")
        self.assertEqual(result.lower().count("anticipatory bail"), 1)


class TestExpansionLength(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_expansion_not_too_long(self):
        """Expansion should be bounded."""
        result = self.expander.expand("bail murder theft fraud")
        words = result.split()
        self.assertLess(len(words), 80)

    def test_max_tokens_limit(self):
        """Should respect max expansion tokens."""
        self.expander._max_expansion_tokens = 10
        result = self.expander.expand("bail")
        words = result.split()
        self.assertLessEqual(len(words), 12)  # 2 original + 10 max


class TestExpandWithEntities(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_adds_act_name(self):
        entities = {
            "acts": ["Indian Penal Code"],
            "sections": [],
            "ipc_sections": [],
            "bns_sections": [],
        }
        result = self.expander.expand_with_entities("Section 302 murder", entities)
        self.assertIn("Indian Penal Code", result)

    def test_adds_section_context(self):
        entities = {
            "acts": [],
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
        }
        result = self.expander.expand_with_entities("murder punishment", entities)
        self.assertIn("section 302", result)

    def test_adds_ipc_section(self):
        entities = {
            "acts": [],
            "sections": [],
            "ipc_sections": ["302"],
            "bns_sections": [],
        }
        result = self.expander.expand_with_entities("murder", entities)
        self.assertIn("section 302 ipc", result)

    def test_no_duplicate_entities(self):
        entities = {
            "acts": ["Indian Penal Code"],
            "sections": ["302"],
            "ipc_sections": [],
            "bns_sections": [],
        }
        result = self.expander.expand_with_entities(
            "Section 302 IPC Indian Penal Code murder", entities
        )
        self.assertEqual(result.lower().count("indian penal code"), 1)


class TestConvenienceFunctions(unittest.TestCase):
    def test_expand_query(self):
        result = expand_query("bail")
        self.assertIn("anticipatory bail", result)

    def test_singleton(self):
        e1 = get_query_expander()
        e2 = get_query_expander()
        self.assertIs(e1, e2)


class TestSpecificLegalTerms(unittest.TestCase):
    """Test expansion for specific legal terms in the dictionary."""

    def setUp(self):
        self.expander = QueryExpander()

    def test_rape_expansion(self):
        result = self.expander.expand("rape punishment")
        self.assertIn("section 376", result)

    def test_anticipatory_bail(self):
        result = self.expander.expand("anticipatory bail")
        self.assertIn("pre-arrest bail", result)

    def test_charge_sheet(self):
        result = self.expander.expand("charge sheet")
        self.assertIn("chargesheet", result)
        self.assertIn("section 173", result)

    def test_maintenance(self):
        result = self.expander.expand("maintenance")
        self.assertIn("alimony", result)
        self.assertIn("section 125", result)

    def test_injunction(self):
        result = self.expander.expand("injunction")
        self.assertIn("stay order", result)
        self.assertIn("order 39", result)

    def test_electronic_evidence(self):
        result = self.expander.expand("electronic evidence")
        self.assertIn("section 65b", result)
        self.assertIn("digital evidence", result)

    def test_fundamental_rights(self):
        result = self.expander.expand("fundamental rights")
        self.assertIn("article 14", result)
        self.assertIn("article 21", result)

    def test_writ(self):
        result = self.expander.expand("writ petition")
        self.assertIn("habeas corpus", result)
        self.assertIn("mandamus", result)


class TestRuntimeSynonyms(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_add_synonym_group(self):
        self.expander.add_synonym_group(
            "custom", ["custom_synonym1", "custom_synonym2"]
        )
        result = self.expander.expand("custom")
        self.assertIn("custom_synonym1", result)
        self.assertIn("custom_synonym2", result)

    def test_get_synonyms(self):
        syns = self.expander.get_synonyms("bail")
        self.assertIn("anticipatory bail", syns)
        self.assertIn("default bail", syns)

    def test_get_synonyms_unknown(self):
        syns = self.expander.get_synonyms("xyznonexistent")
        self.assertEqual(syns, [])


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.expander = QueryExpander()

    def test_case_insensitive(self):
        """Expansion should work regardless of case."""
        result1 = self.expander.expand("BAIL")
        result2 = self.expander.expand("bail")
        # Both should contain the same synonyms (lowercase)
        self.assertIn("anticipatory bail", result1.lower())
        self.assertIn("anticipatory bail", result2.lower())

    def test_partial_match_no_expand(self):
        """'ba' should not match 'bail'."""
        result = self.expander.expand("ba")
        self.assertEqual(result, "ba")

    def test_phrase_match(self):
        """Multi-word phrases should match."""
        result = self.expander.expand("anticipatory bail")
        self.assertIn("pre-arrest bail", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
