"""
Tests for HECTOR Section-Aware Legal Chunker (Phase 1)
Validates section-level splitting and denormalized context.
Uses unittest (no pytest dependency).
"""

import unittest
from core.legal_chunker import SectionAwareChunker, chunk_legal_page


class TestSectionSplitting(unittest.TestCase):
    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_single_section(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder shall be punished with death."
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertEqual(len(chunks), 1)
        self.assertIn("302", chunks[0]["section_number"])

    def test_multiple_sections(self):
        text = """Section 302. Punishment for murder.
Whoever commits murder shall be punished with death.

Section 303. Punishment for murder by life-convict.
Whoever commits murder while under sentence of imprisonment for life shall be punished with death."""
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertGreaterEqual(len(chunks), 2)
        self.assertIn("302", chunks[0]["section_number"])
        self.assertIn("303", chunks[1]["section_number"])

    def test_section_with_number_dot_format(self):
        text = """420. Cheating and dishonestly inducing delivery of property.
Whoever shall cheat and dishonestly induce the property shall be punished."""
        chunks = self.chunker.chunk_page(text)
        self.assertEqual(len(chunks), 1)
        self.assertIn("420", chunks[0]["section_number"])

    def test_no_sections_returns_single_chunk(self):
        text = "This is a preamble with no section numbers. It explains the purpose of the act."
        chunks = self.chunker.chunk_page(text)
        self.assertEqual(len(chunks), 1)

    def test_empty_text(self):
        chunks = self.chunker.chunk_page("")
        self.assertEqual(len(chunks), 0)

    def test_whitespace_only(self):
        chunks = self.chunker.chunk_page("   \n\n   ")
        self.assertEqual(len(chunks), 0)


class TestDenormalizedContext(unittest.TestCase):
    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_act_name_prepended(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertTrue(chunks[0]["content"].startswith("[Indian Penal Code"))

    def test_chapter_prepended(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = self.chunker.chunk_page(
            text, act_name="Indian Penal Code", chapter="Chapter XVII"
        )
        self.assertIn("Chapter XVII", chunks[0]["content"])

    def test_section_prepended(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertIn("Section 302", chunks[0]["content"])

    def test_context_format(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = self.chunker.chunk_page(
            text, act_name="Indian Penal Code", chapter="Chapter XVII"
        )
        content = chunks[0]["content"]
        # Should start with [Act | Chapter | Section]
        self.assertTrue(content.startswith("["))
        self.assertIn("Indian Penal Code", content)
        self.assertIn("Chapter XVII", content)
        self.assertIn("Section 302", content)

    def test_section_title_in_context(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertIn("Punishment for murder", chunks[0]["content"])


class TestMetadataExtraction(unittest.TestCase):
    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_proviso_detected(self):
        text = """Section 302. Punishment for murder.
Whoever commits murder shall be punished with death:
Provided that nothing in this section shall apply to causing death of a person under 18."""
        chunks = self.chunker.chunk_page(text)
        self.assertTrue(chunks[0]["has_proviso"])

    def test_exception_detected(self):
        text = """Section 302. Punishment for murder.
Whoever commits murder shall be punished with death.
Exception: This does not apply to acts done by public servants."""
        chunks = self.chunker.chunk_page(text)
        self.assertTrue(chunks[0]["has_exception"])

    def test_illustration_detected(self):
        text = """Section 302. Punishment for murder.
Whoever commits murder shall be punished with death.
Illustration: A shoots B with intent to kill."""
        chunks = self.chunker.chunk_page(text)
        self.assertTrue(chunks[0]["has_illustration"])

    def test_section_number_extracted(self):
        text = "Section 420. Cheating.\nWhoever cheats shall be punished."
        chunks = self.chunker.chunk_page(text)
        self.assertEqual(chunks[0]["section_number"], "420")

    def test_section_title_extracted(self):
        text = "Section 420. Cheating and dishonestly inducing delivery of property.\nWhoever cheats..."
        chunks = self.chunker.chunk_page(text)
        self.assertIn("Cheating", chunks[0]["section_title"])


class TestLongSectionSplitting(unittest.TestCase):
    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_long_section_split_at_subsections(self):
        # Create a section with many subsections
        text = "Section 1. Definitions.\n"
        for i in range(20):
            text += f"({i}) Sub-section {i} with some content that makes it longer. "
            text += "Additional text to make this subsection substantial enough to be meaningful. "
            text += "More text here to ensure the section exceeds the maximum length. "

        chunks = self.chunker.chunk_page(text)
        # Should be split into multiple chunks
        self.assertGreater(len(chunks), 1)
        # All should have section number 1
        for chunk in chunks:
            self.assertEqual(chunk["section_number"], "1")


class TestShortSectionMerging(unittest.TestCase):
    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_short_section_merged(self):
        text = """Section 302. Punishment for murder.
Whoever commits murder shall be punished with death.

303.

Section 304. Punishment for culpable homicide.
Whoever commits culpable homicide shall be punished with imprisonment."""
        chunks = self.chunker.chunk_page(text)
        # Section 303 is too short, should be merged
        self.assertGreaterEqual(len(chunks), 1)


class TestConvenienceFunction(unittest.TestCase):
    def test_chunk_legal_page(self):
        text = "Section 302. Punishment for murder.\nWhoever commits murder..."
        chunks = chunk_legal_page(text, act_name="Indian Penal Code")
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        self.assertIn("Indian Penal Code", chunks[0]["content"])


class TestRealWorldPatterns(unittest.TestCase):
    """Test with realistic Indian legal text patterns."""

    def setUp(self):
        self.chunker = SectionAwareChunker()

    def test_ipc_style(self):
        text = """Indian Penal Code, 1860

Section 302. Punishment for murder.—Whoever commits murder shall be
punished with death, or imprisonment for life, and shall also be
liable to fine.

Section 303. Punishment for murder by life-convict.—Whoever commits
murder while under sentence of imprisonment for life shall be
punished with death."""
        chunks = self.chunker.chunk_page(text, act_name="Indian Penal Code")
        self.assertEqual(len(chunks), 2)
        self.assertIn("302", chunks[0]["section_number"])
        self.assertIn("303", chunks[1]["section_number"])

    def test_bns_style(self):
        text = """Bharatiya Nyaya Sanhita, 2023

Section 101. Murder.—Whoever commits murder shall be punished
with death or imprisonment for life, and shall also be liable to fine.

Section 103. Culpable homicide not amounting to murder.—Whoever
commits culpable homicide shall be punished with imprisonment."""
        chunks = self.chunker.chunk_page(text, act_name="Bharatiya Nyaya Sanhita")
        self.assertEqual(len(chunks), 2)
        self.assertIn("101", chunks[0]["section_number"])
        self.assertIn("103", chunks[1]["section_number"])

    def test_with_proviso(self):
        text = """Section 498A. Husband or relative of husband of woman subjecting her to cruelty.—
Whoever, whether before or after the marriage to such woman, subjects her to cruelty
shall be punished with imprisonment.

Provided that nothing in this section shall apply to any matter which is subject to
any civil or criminal proceeding."""
        chunks = self.chunker.chunk_page(text)
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0]["has_proviso"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
