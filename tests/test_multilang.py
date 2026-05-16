"""
Unit tests for Multi-Language Support Module.
Tests Hindi/English translation and transliteration.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.multilang import (
    MultiLanguageProcessor,
    HindiLegalOCR,
    BilingualQuery,
    create_hindi_search_query,
)


class TestMultiLanguageProcessor:
    """Test multi-language processing."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return MultiLanguageProcessor()

    def test_processor_initialization(self, processor):
        """Test processor initializes correctly."""
        assert processor is not None
        assert hasattr(processor, 'legal_terms')
        assert hasattr(processor, 'hindi_numbers')

    def test_detect_language_english(self, processor):
        """Test English language detection."""
        result = processor.detect_language("This is a test")
        assert result == "english"

    def test_detect_language_hindi(self, processor):
        """Test Hindi language detection."""
        result = processor.detect_language("यह एक परीक्षण है")
        assert result == "hindi"

    def test_detect_language_mixed(self, processor):
        """Test mixed language detection."""
        result = processor.detect_language("Test परीक्षण")
        assert result in ["english", "mixed", "hindi"]

    def test_detect_language_empty(self, processor):
        """Test empty string detection."""
        result = processor.detect_language("")
        assert result == "english"

    def test_translate_to_hindi(self, processor):
        """Test English to Hindi translation."""
        result = processor.translate_to_hindi("murder")
        assert "हत्या" in result

    def test_translate_to_hindi_section(self, processor):
        """Test section translation."""
        result = processor.translate_to_hindi("section 302")
        assert "धारा" in result

    def test_translate_to_english(self, processor):
        """Test Hindi to English translation."""
        result = processor.translate_to_english("हत्या")
        assert "murder" in result

    def test_transliterate_to_itrans(self, processor):
        """Test Devanagari to ITRANS."""
        result = processor.transliterate_to_itrans("हत्या")
        assert isinstance(result, str)

    def test_transliterate_from_itrans(self, processor):
        """Test ITRANS to Devanagari."""
        result = processor.transliterate_from_itrans("hatya")
        assert isinstance(result, str)

    def test_create_bilingual_search_english(self, processor):
        """Test bilingual search creation from English."""
        result = processor.create_bilingual_search("murder")
        assert result.english == "murder"
        assert result.hindi is not None

    def test_create_bilingual_search_hindi(self, processor):
        """Test bilingual search creation from Hindi."""
        result = processor.create_bilingual_search("हत्या")
        assert result.hindi == "हत्या"
        assert result.english is not None

    def test_normalize_legal_term_english(self, processor):
        """Test legal term normalization (English)."""
        result = processor.normalize_legal_term("murder")
        assert result == "murder"

    def test_normalize_legal_term_hindi(self, processor):
        """Test legal term normalization (Hindi)."""
        result = processor.normalize_legal_term("हत्या")
        assert result == "murder"


class TestHindiLegalOCR:
    """Test Hindi legal OCR."""

    @pytest.fixture
    def ocr(self):
        """Create OCR instance."""
        return HindiLegalOCR()

    def test_ocr_initialization(self, ocr):
        """Test OCR initializes correctly."""
        assert ocr is not None
        assert hasattr(ocr, 'DOCUMENT_PATTERNS')

    def test_detect_document_type_fir(self, ocr):
        """Test FIR document detection."""
        result = ocr.detect_document_type("प्रथम सूचना रिपोर्ट")
        assert result == "fir"

    def test_detect_document_type_judgment(self, ocr):
        """Test judgment document detection."""
        result = ocr.detect_document_type("यह एक निर्णय है")
        assert result == "judgment"

    def test_detect_document_type_unknown(self, ocr):
        """Test unknown document type."""
        result = ocr.detect_document_type("random text")
        assert result is None

    def test_extract_sections_devanagari(self, ocr):
        """Test section extraction from Devanagari."""
        text = "धारा 302 के अनुसार"
        result = ocr.extract_sections(text)
        assert len(result) > 0
        assert result[0]['number'] == "302"

    def test_extract_sections_english(self, ocr):
        """Test section extraction from English."""
        text = "Section 302 of IPC"
        result = ocr.extract_sections(text)
        assert len(result) > 0


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_hindi_search_query(self):
        """Test Hindi search query creation."""
        english, hindi = create_hindi_search_query("murder")
        assert english == "murder"
        assert hindi != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])