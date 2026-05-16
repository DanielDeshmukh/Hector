"""
Multi-Language Support Module for HECTOR.
Handles Hindi and regional language legal texts.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever

# Hindi translations for common legal terms
HINDI_LEGAL_TERMS = {
    # Criminal law
    "murder": "हत्या",
    "theft": "चोरी",
    "robbery": "डकैती",
    "rape": "बलात्कार",
    "assault": "हमला",
    "kidnapping": "अपहरण",
    "extortion": "उगाही",
    "forgery": "जालसाजी",
    "cheating": "धोखाधड़ी",
    "criminal breach of trust": "आपराधिक विश्वासघात",
    "private defence": "स्वप्रतिरक्षा",
    "abetment": "उकसाना",
    "conspiracy": "षड्यंत्र",
    "offence": "अपराध",
    "punishment": "दंड",
    "imprisonment": "कारावास",
    "fine": "जुर्माना",
    "bail": "जमानत",
    "arrest": "गिरफ्तारी",
    "investigation": "जांच",
    "trial": "विचारण",
    "judgment": "निर्णय",
    "appeal": "अपील",
    "sentence": "सजा",
    "acquittal": "रिहाई",
    "conviction": "सिद्धांत",
    " FIR": "प्रथम सूचना रिपोर्ट",
    "cognizable": "संज्ञेय",
    "non-cognizable": "असंज्ञेय",
    "compoundable": "समझौता योग्य",
    "non-compoundable": "असमझौता योग्य",
    "warrant": "वारंट",
    "summons": "समन",
    "charge": "आरोप",
    "evidence": "साक्ष्य",
    "witness": "गवाह",
    "statement": "बयान",
    "confession": "स्वीकारोक्ति",
    # Court terms
    "supreme court": "सर्वोच्च न्यायालय",
    "high court": "उच्च न्यायालय",
    "district court": "जिला न्यायालय",
    "magistrate": "मजिस्ट्रेट",
    "judge": "न्यायाधीश",
    "advocate": "वकील",
    "plaintiff": "वादी",
    "defendant": "प्रतिवादी",
    "accused": "आरोपी",
    "complainant": "शिकायतकर्ता",
    "court": "न्यायालय",
    "bar association": "बार संघ",
    # Civil terms
    "civil": "नागरिक",
    "suit": "वाद",
    "decree": "आदेश",
    "execution": "निष्पादन",
    "decree holder": "आदेशधारक",
    "judgment debtor": "ऋणी",
    "limitation": "सीमा",
    "mesne profit": "मध्यवर्ती लाभ",
    "injunction": "याचिका",
    # Property
    "property": "संपत्ति",
    "land": "भूमि",
    "house": "मकान",
    "rent": "किराया",
    "tenant": "किरायेदार",
    "landlord": "मकान मालिक",
    # Family
    "marriage": "विवाह",
    "divorce": "तलाक",
    "maintenance": "गुजारा",
    "alimony": "वैवाहिक भरण",
    "guardianship": "संरक्षण",
    "succession": "उत्तराधिकार",
    "inheritance": "विरासत",
    "will": "वसीयत",
    # General
    "law": "कानून",
    "act": "अधिनियम",
    "section": "धारा",
    "chapter": "अध्याय",
    "article": "अनुच्छेद",
    "clause": "खंड",
    "schedule": "अनुसूची",
}

# Hindi number mappings
HINDI_NUMBERS = {
    "ek": "1", "do": "2", "teen": "3", "char": "4", "paanch": "5",
    "chah": "6", "saat": "7", "aath": "8", "nau": "9", "das": "10",
    "gyarah": "11", "barah": "12", "terah": "13", "choudah": "14",
    "pandrah": "15", "solah": "16", "satrah": "17", "atharah": "18",
    "unnis": "19", "bees": "20",
}

# Devanagari to ITRANS mapping
DEVANAGARI_TO_ITRANS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 'T', 'ठ': 'Th', 'ड': 'D', 'ढ': 'Dh', 'ण': 'N',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'Sh',
    'स': 's', 'ह': 'h',
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'n', 'ः': 'h',
}

# Common legal Hindi phrases
HINDI_PHRASES = {
    "section": "धारा",
    "according to law": "कानून के अनुसार",
    "in the opinion of": "की राय में",
    "it is held": "यह अभिलिखित है",
    "it is observed": "यह अवलोकन किया जाता है",
    "in the light of": "के प्रकाश में",
    "due to": "के कारण",
    "without prejudice": "बिना पूर्वाग्रह के",
    "mutatis mutandis": "आवश्यक परिवर्तनों सहित",
    "prima facie": "प्रथम दृष्ट्या",
    "res judicata": "विचाराधीन विषय",
    " locus standi": "स्थिति का अधिकार",
    "cause of action": "कार्य का कारण",
    "limitation period": "सीमा अवधि",
}


@dataclass
class BilingualQuery:
    """Represents a query with English and Hindi variants."""
    english: str
    hindi: str | None = None
    transliteration: str | None = None


class MultiLanguageProcessor:
    """Processes multi-language legal queries."""

    def __init__(self, retriever: "HectorHybridRetriever | None" = None):
        self.retriever = retriever
        self.legal_terms = HINDI_LEGAL_TERMS
        self.hindi_numbers = HINDI_NUMBERS

    def detect_language(self, text: str) -> str:
        """Detect if text is in English, Hindi, or mixed."""
        hindi_chars = 0
        english_chars = 0

        # Check for Devanagari script
        for char in text:
            if 'ऀ' <= char <= 'ॿ':  # Devanagari range
                hindi_chars += 1
            elif char.isalpha():
                english_chars += 1

        total = hindi_chars + english_chars
        if total == 0:
            return "english"

        hindi_ratio = hindi_chars / total

        if hindi_ratio > 0.5:
            return "hindi"
        elif hindi_ratio > 0.1:
            return "mixed"
        return "english"

    def translate_to_hindi(self, text: str) -> str:
        """Translate English legal terms to Hindi."""
        words = text.lower().split()
        translated = []

        for word in words:
            # Check for exact match
            if word in self.legal_terms:
                translated.append(self.legal_terms[word])
            else:
                # Check for partial matches
                found = False
                for eng, hin in self.legal_terms.items():
                    if eng in word:
                        translated.append(hin)
                        found = True
                        break
                if not found:
                    translated.append(word)

        return " ".join(translated)

    def translate_to_english(self, hindi_text: str) -> str:
        """Translate Hindi legal terms to English."""
        words = hindi_text.split()
        translated = []

        for word in words:
            # Reverse lookup
            found = False
            for eng, hin in self.legal_terms.items():
                if hin == word:
                    translated.append(eng)
                    found = True
                    break
            if not found:
                translated.append(word)

        return " ".join(translated)

    def transliterate_to_itrans(self, devanagari: str) -> str:
        """Convert Devanagari to ITRANS."""
        result = []
        for char in devanagari:
            if char in DEVANAGARI_TO_ITRANS:
                result.append(DEVANAGARI_TO_ITRANS[char])
            else:
                result.append(char)
        return "".join(result)

    def transliterate_from_itrans(self, itrans: str) -> str:
        """Convert ITRANS to Devanagari."""
        # Create reverse mapping
        itrans_to_dev = {v: k for k, v in DEVANAGARI_TO_ITRANS.items()}
        # Add common combinations
        itrans_to_dev.update({
            'aa': 'ा', 'ee': 'ी', 'oo': 'ू', 'ai': 'ै', 'au': 'ौ',
            'kh': 'ख', 'gh': 'घ', 'chh': 'छ', 'jh': 'झ',
            'th': 'थ', 'dh': 'ध', 'ph': 'फ', 'bh': 'भ',
            'sh': 'श', 'Sh': 'ष',
        })

        result = []
        i = 0
        while i < len(itrans):
            # Try 3-char match
            if i + 3 <= len(itrans) and itrans[i:i+3] in itrans_to_dev:
                result.append(itrans_to_dev[itrans[i:i+3]])
                i += 3
            # Try 2-char match
            elif i + 2 <= len(itrans) and itrans[i:i+2] in itrans_to_dev:
                result.append(itrans_to_dev[itrans[i:i+2]])
                i += 2
            else:
                result.append(itrans[i])
                i += 1

        return "".join(result)

    def create_bilingual_search(self, query: str) -> BilingualQuery:
        """Create a bilingual query with all variants."""
        lang = self.detect_language(query)

        if lang == "english":
            english = query
            hindi = self.translate_to_hindi(query)
            transliteration = self.transliterate_to_itrans(hindi) if hindi else None
        elif lang == "hindi":
            hindi = query
            english = self.translate_to_english(query)
            transliteration = self.transliterate_to_itrans(query) if self.detect_language(query) == "hindi" else None
        else:  # mixed
            english = query
            hindi = None
            transliteration = None

        return BilingualQuery(
            english=english,
            hindi=hindi,
            transliteration=transliteration,
        )

    def search_bilingual(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:
        """Search with both English and Hindi variants."""
        bilingual = self.create_bilingual_search(query)

        all_results = []

        # Search English
        if self.retriever:
            eng_results = self.retriever.search(bilingual.english, top_k=top_k)
            all_results.extend(eng_results)

            # Search Hindi if available
            if bilingual.hindi:
                hin_results = self.retriever.search(bilingual.hindi, top_k=top_k)
                # Add language tag
                for r in hin_results:
                    r["language"] = "hindi"
                all_results.extend(hin_results)

        # Deduplicate by ID
        seen = set()
        unique_results = []
        for r in all_results:
            if r.get("id") not in seen:
                seen.add(r.get("id"))
                unique_results.append(r)

        return unique_results[:top_k]

    def normalize_legal_term(self, term: str) -> str:
        """Normalize a legal term across languages."""
        term_lower = term.lower()

        # Check English
        if term_lower in self.legal_terms:
            return term_lower

        # Check Hindi reverse
        for eng, hin in self.legal_terms.items():
            if hin == term_lower:
                return eng

        # Check Hindi numbers
        if term_lower in self.hindi_numbers:
            return self.hindi_numbers[term_lower]

        return term_lower


class HindiLegalOCR:
    """OCR support for Hindi legal documents."""

    # Common Hindi legal document patterns
    DOCUMENT_PATTERNS = {
        "fir": ["प्रथम सूचना रिपोर्ट", "FIR"],
        "charge_sheet": ["आरोप पत्र", "चार्जशीट"],
        "judgment": ["निर्णय", "Judgment"],
        "petition": ["याचिका", "Petition"],
        "affidavit": ["हलफनामा", "Affidavit"],
        "contract": ["अनुबंध", "Contract"],
        "notice": ["नोटिस", "Notice"],
    }

    def detect_document_type(self, text: str) -> str | None:
        """Detect the type of Hindi legal document."""
        for doc_type, keywords in self.DOCUMENT_PATTERNS.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    return doc_type
        return None

    def extract_sections(self, text: str) -> list[dict]:
        """Extract section numbers from Hindi text."""
        import re

        # Match Devanagari numbers followed by धारा or sections
        patterns = [
            r"(\d+)\s*धारा",
            r"धारा\s*(\d+)",
            r"(\d+)\s*Section",
            r"Section\s*(\d+)",
        ]

        sections = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sections.append({
                    "number": match.group(1),
                    "context": text[max(0, match.start()-20):match.end()+20],
                })

        return sections


def create_hindi_search_query(english_query: str) -> tuple[str, str]:
    """Helper to create Hindi search query from English."""
    processor = MultiLanguageProcessor()
    bilingual = processor.create_bilingual_search(english_query)
    return bilingual.english, bilingual.hindi or ""