"""
Tests for HECTOR Structured Query Parser (Phase A)
Validates legal entity extraction from user queries.
Uses unittest (no pytest dependency).
"""

import unittest
from core.query_parser import LegalQueryParser, LegalEntities, parse_query, expand_legal_query


class TestSectionExtraction(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_section_with_ipc(self):
        entities = self.parser.parse("What is Section 302 IPC punishment?")
        self.assertIn("302", entities.ipc_sections)
        self.assertGreater(entities.confidence, 0.5)

    def test_section_with_bns(self):
        entities = self.parser.parse("Section 101 BNS culpable homicide")
        self.assertIn("101", entities.bns_sections)

    def test_section_standalone(self):
        entities = self.parser.parse("What does Section 144 say?")
        self.assertIn("144", entities.sections)

    def test_section_with_of_ipc(self):
        entities = self.parser.parse("Section 376 of IPC rape punishment")
        self.assertIn("376", entities.ipc_sections)

    def test_multiple_sections(self):
        entities = self.parser.parse("Sections 302 and 376 IPC murder and rape")
        self.assertIn("302", entities.ipc_sections)
        self.assertIn("376", entities.ipc_sections)

    def test_section_bracket_notation(self):
        entities = self.parser.parse("[s 302] murder punishment")
        self.assertIn("302", entities.sections)

    def test_section_shorthand(self):
        entities = self.parser.parse("Sec. 498A cruelty")
        self.assertIn("498a", entities.sections)


class TestActExtraction(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_ipc_act(self):
        entities = self.parser.parse("Indian Penal Code murder punishment")
        self.assertIn("Indian Penal Code", entities.acts)

    def test_bns_act(self):
        entities = self.parser.parse("Bharatiya Nyaya Sanhita theft punishment")
        self.assertIn("Bharatiya Nyaya Sanhita", entities.acts)

    def test_crpc_act(self):
        entities = self.parser.parse("Code of Criminal Procedure bail provisions")
        self.assertIn("Code of Criminal Procedure", entities.acts)

    def test_evidence_act(self):
        entities = self.parser.parse("Indian Evidence Act Section 65B")
        self.assertIn("Indian Evidence Act", entities.acts)

    def test_ipc_abbreviation(self):
        entities = self.parser.parse("IPC Section 302 murder")
        self.assertIn("Indian Penal Code", entities.acts)

    def test_bns_abbreviation(self):
        entities = self.parser.parse("BNS theft punishment")
        self.assertIn("Bharatiya Nyaya Sanhita", entities.acts)

    def test_multiple_acts(self):
        entities = self.parser.parse("Compare IPC 302 with BNS 101")
        self.assertIn("Indian Penal Code", entities.acts)
        self.assertIn("Bharatiya Nyaya Sanhita", entities.acts)


class TestTopicExtraction(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_bail_topic(self):
        entities = self.parser.parse("When can I get bail?")
        self.assertIn("bail", entities.topics)

    def test_anticipatory_bail(self):
        entities = self.parser.parse("How to get anticipatory bail?")
        self.assertIn("anticipatory_bail", entities.topics)

    def test_divorce_topic(self):
        entities = self.parser.parse("How to file for divorce?")
        self.assertIn("divorce", entities.topics)

    def test_murder_topic(self):
        entities = self.parser.parse("What is punishment for murder?")
        self.assertIn("murder", entities.topics)

    def test_fir_topic(self):
        entities = self.parser.parse("How to file an FIR?")
        self.assertIn("fir", entities.topics)


class TestArticleExtraction(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_article_21(self):
        entities = self.parser.parse("Article 21 right to life")
        self.assertIn("21", entities.articles)

    def test_article_14(self):
        entities = self.parser.parse("Article 14 equality before law")
        self.assertIn("14", entities.articles)


class TestCourtExtraction(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_supreme_court(self):
        entities = self.parser.parse("What did the Supreme Court say?")
        self.assertIn("Supreme Court of India", entities.courts)

    def test_high_court(self):
        entities = self.parser.parse("Appeal to High Court")
        self.assertIn("High Court", entities.courts)


class TestConfidence(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_no_entities_low_confidence(self):
        entities = self.parser.parse("Hello how are you?")
        self.assertEqual(entities.confidence, 0.0)

    def test_single_entity_moderate_confidence(self):
        entities = self.parser.parse("bail")
        self.assertGreaterEqual(entities.confidence, 0.5)
        self.assertLessEqual(entities.confidence, 0.7)

    def test_multiple_entities_high_confidence(self):
        entities = self.parser.parse("Section 302 IPC murder punishment")
        self.assertGreaterEqual(entities.confidence, 0.8)


class TestQueryExpansion(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_expansion_adds_act(self):
        expanded = expand_legal_query("Section 302 IPC murder punishment")
        self.assertIn("Indian Penal Code", expanded)

    def test_expansion_preserves_original(self):
        original = "Section 302 IPC murder"
        expanded = expand_legal_query(original)
        self.assertIn(original, expanded)

    def test_expansion_no_duplicates(self):
        expanded = expand_legal_query("Section 302 IPC murder")
        self.assertLessEqual(expanded.lower().count("section 302"), 1)


class TestRouteHint(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_hint_for_sections(self):
        entities = self.parser.parse("Section 302 IPC")
        self.assertEqual(self.parser.get_route_hint(entities), "LEGAL_RESEARCH")

    def test_hint_for_acts(self):
        entities = self.parser.parse("Indian Evidence Act")
        self.assertEqual(self.parser.get_route_hint(entities), "LEGAL_RESEARCH")

    def test_hint_for_topics(self):
        entities = self.parser.parse("bail")
        self.assertEqual(self.parser.get_route_hint(entities), "LEGAL_RESEARCH")

    def test_none_hint(self):
        entities = self.parser.parse("Hello world")
        self.assertIsNone(self.parser.get_route_hint(entities))


class TestConvenienceFunctions(unittest.TestCase):
    def test_parse_query(self):
        entities = parse_query("Section 302 IPC murder")
        self.assertIsInstance(entities, LegalEntities)
        self.assertIn("302", entities.ipc_sections)

    def test_expand_legal_query(self):
        expanded = expand_legal_query("Section 302 IPC murder")
        self.assertIn("Indian Penal Code", expanded)


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.parser = LegalQueryParser()

    def test_empty_query(self):
        entities = self.parser.parse("")
        self.assertEqual(entities.confidence, 0.0)
        self.assertEqual(len(entities.sections), 0)

    def test_no_legal_content(self):
        entities = self.parser.parse("What is the weather today?")
        self.assertEqual(entities.confidence, 0.0)
        self.assertEqual(len(entities.acts), 0)

    def test_mixed_legal_and_non_legal(self):
        entities = self.parser.parse("I'm feeling sad, can I get bail?")
        self.assertIn("bail", entities.topics)
        self.assertGreater(entities.confidence, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
