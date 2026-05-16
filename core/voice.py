"""
Voice Query Interface for HECTOR.
Enables voice-based legal research with speech recognition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable
import re

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


# Legal voice commands
VOICE_COMMANDS = {
    "search": ["search", "find", "look up", "query", "research"],
    "compare": ["compare", "versus", "vs", "difference between"],
    "cite": ["citation", "cite", "reference", "source"],
    "bail": ["bail", "anticipatory bail", "regular bail"],
    "section": ["section", "section under", " IPC", " BNS"],
    "help": ["help", "commands", "what can you do"],
    "exit": ["exit", "quit", "stop", "close"],
}


@dataclass
class VoiceQuery:
    """Represents a processed voice query."""
    raw_text: str
    normalized_text: str
    command: str | None
    confidence: float
    legal_terms: list[str] = field(default_factory=list)


class LegalTermNormalizer:
    """Normalizes legal terminology from speech input."""

    # Common speech-to-text corrections for legal terms
    CORRECTIONS = {
        "ipc": "IPC",
        "bns": "BNS",
        "crpc": "CRPC",
        "bnss": "BNSS",
        "bsa": "BSA",
        "section": "Section",
        "article": "Article",
        "act": "Act",
        "fir": "FIR",
        "f i r": "FIR",
    }

    # Legal term expansions
    EXPANSIONS = {
        "murder": "murder (Section 302 BNS)",
        "theft": "theft (Section 318 BNS)",
        "robbery": "robbery (Section 309 BNS)",
        "bail": "bail under Section 437 CrPC",
        "cognizable": "cognizable offence",
        "non cognizable": "non-cognizable offence",
        "compoundable": "compoundable offence",
        "bailable": "bailable offence",
        "non bailable": "non-bailable offence",
    }

    def normalize(self, text: str) -> str:
        """Normalize legal terminology in text."""
        normalized = text.lower().strip()

        # Apply corrections
        for wrong, correct in self.CORRECTIONS.items():
            normalized = re.sub(rf'\b{wrong}\b', correct, normalized, flags=re.IGNORECASE)

        # Apply expansions
        for term, expansion in self.EXPANSIONS.items():
            if term in normalized:
                normalized = normalized.replace(term, expansion)

        return normalized

    def extract_legal_terms(self, text: str) -> list[str]:
        """Extract legal terms from text."""
        terms = []
        text_lower = text.lower()

        # Extract section numbers
        section_matches = re.findall(r'section\s*(\d+)', text_lower)
        for match in section_matches:
            terms.append(f"Section {match}")

        # Extract IPC/BNS sections
        act_matches = re.findall(r'(ipc|bns|crpc|bnss|bsa)\s*section?\s*(\d+)', text_lower)
        for act, num in act_matches:
            terms.append(f"{act.upper()} Section {num}")

        # Extract act names
        for act in ["BNS", "BNSS", "BSA", "IPC", "CRPC", "CPC", "IEA"]:
            if act.lower() in text_lower:
                terms.append(act)

        # Extract legal keywords
        legal_keywords = [
            "bail", "arrest", " FIR", "cognizable", "non-cognizable",
            "compoundable", "warrant", "summons", "charge", "evidence",
            "witness", "judgment", "appeal", "offence", "punishment",
        ]
        for kw in legal_keywords:
            if kw in text_lower:
                terms.append(kw)

        return list(set(terms))


class VoiceCommandProcessor:
    """Processes voice commands and routes to appropriate handlers."""

    def __init__(self):
        self.commands = VOICE_COMMANDS
        self.normalizer = LegalTermNormalizer()

    def detect_command(self, text: str) -> tuple[str | None, float]:
        """Detect the command type from voice input."""
        text_lower = text.lower()

        for command, keywords in self.commands.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Calculate confidence based on keyword position
                    position = text_lower.find(keyword)
                    position_score = 1.0 - (position / max(len(text_lower), 1))
                    confidence = 0.7 + (0.3 * position_score)
                    return command, min(confidence, 1.0)

        return None, 0.3

    def parse_voice_query(self, raw_text: str) -> VoiceQuery:
        """Parse raw voice input into structured query."""
        normalized = self.normalizer.normalize(raw_text)
        command, confidence = self.detect_command(normalized)
        legal_terms = self.normalizer.extract_legal_terms(normalized)

        return VoiceQuery(
            raw_text=raw_text,
            normalized_text=normalized,
            command=command,
            confidence=confidence,
            legal_terms=legal_terms,
        )


class VoiceQueryHandler:
    """Handles voice query processing and execution."""

    def __init__(self, retriever: "HectorHybridRetriever | None" = None):
        self.retriever = retriever
        self.command_processor = VoiceCommandProcessor()
        self.query_history: list[VoiceQuery] = []

    def process_voice_query(self, audio_data: bytes | None = None, text: str | None = None) -> VoiceQuery:
        """
        Process voice input (either audio or direct text).

        Args:
            audio_data: Raw audio bytes (for future STT integration)
            text: Direct text input (bypassing speech recognition)

        Returns:
            Processed VoiceQuery object
        """
        # For now, accept text input
        # In production, this would integrate with:
        # - Web Speech API (browser)
        # - Whisper API (server-side)
        # - Vosk (offline)

        if text is None:
            raise ValueError("Either audio_data or text must be provided")

        voice_query = self.command_processor.parse_voice_query(text)
        self.query_history.append(voice_query)

        return voice_query

    def execute_search(self, query: VoiceQuery) -> list[dict]:
        """Execute search based on voice query."""
        if self.retriever is None:
            return []

        return self.retriever.search(query.normalized_text, top_k=5)

    def get_query_history(self) -> list[VoiceQuery]:
        """Get all voice queries in history."""
        return self.query_history

    def clear_history(self) -> None:
        """Clear voice query history."""
        self.query_history.clear()

    def get_last_query(self) -> VoiceQuery | None:
        """Get the most recent voice query."""
        return self.query_history[-1] if self.query_history else None


def get_voice_help_text() -> str:
    """Get help text for voice commands."""
    return """
🎤 Voice Commands for HECTOR:

• "Search [topic]" - Start a legal research query
• "Compare [section A] versus [section B]" - Compare IPC vs BNS
• "Find [topic] citation" - Get case citations
• "Bail information" - Get bail-related provisions
• "Section 302" - Look up specific section
• "Help" - Show this menu
• "Exit" - Quit the application

Examples:
- "Search for murder under BNS"
- "Compare section 302 IPC versus section 302 BNS"
- "Find bail provisions under CRPC"
"""


class VoiceQueryCLI:
    """CLI wrapper for voice queries."""

    def __init__(self, handler: VoiceQueryHandler):
        self.handler = handler
        self.running = False

    def start(self) -> None:
        """Start the voice CLI loop."""
        self.running = True
        print(get_voice_help_text())

        while self.running:
            try:
                user_input = input("\n🎤 Speak or type your query: ").strip()

                if not user_input:
                    continue

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "stop", "close"]:
                    self.running = False
                    print("Goodbye!")
                    break

                # Process the query
                voice_query = self.handler.process_voice_query(text=user_input)

                print(f"\n📝 Detected command: {voice_query.command or 'search'}")
                print(f"📋 Normalized: {voice_query.normalized_text}")

                if voice_query.legal_terms:
                    print(f"⚖️  Legal terms: {', '.join(voice_query.legal_terms)}")

                # Execute based on command
                if voice_query.command == "help":
                    print(get_voice_help_text())
                elif voice_query.command == "compare":
                    # Extract sections for comparison
                    results = self.handler.execute_search(voice_query)
                    print(f"\n🔍 Found {len(results)} relevant sections")
                    for r in results[:3]:
                        print(f"  - {r.get('title', 'Unknown')}")
                elif voice_query.command in ["search", "bail", "section", "cite"]:
                    results = self.handler.execute_search(voice_query)
                    print(f"\n🔍 Found {len(results)} results")
                    for r in results[:5]:
                        print(f"  - {r.get('title', 'Unknown')}")
                else:
                    results = self.handler.execute_search(voice_query)
                    print(f"\n🔍 Found {len(results)} results")
                    for r in results[:3]:
                        print(f"  - {r.get('title', 'Unknown')}")

            except KeyboardInterrupt:
                self.running = False
                print("\nGoodbye!")
            except Exception as e:
                print(f"Error: {e}")

    def print_history(self) -> None:
        """Print voice query history."""
        history = self.handler.get_query_history()
        if not history:
            print("No query history.")
            return

        print("\n📜 Voice Query History:")
        for i, q in enumerate(history, 1):
            print(f"  {i}. {q.normalized_text} (command: {q.command}, confidence: {q.confidence:.2f})")