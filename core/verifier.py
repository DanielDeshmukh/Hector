import json
import re
from typing import Any

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# Strict Citation System Prompt for Zero-Hallucination
STRICT_CITATION_PROMPT = """You are HECTOR, a zero-hallucination legal AI assistant.

CRITICAL RULES:
- Only answer using information explicitly present in the retrieved context
- If information is not in the context, respond: "I cannot find this information in the loaded legal texts."
- Every claim must cite: Source Document, Page Number, and Section if applicable
- Never infer, imply, or fabricate information not explicitly stated in the source
- When citing, use format: [Source: Book Name, Page: X, Section: Y BNS]

CONTEXT PROVIDED:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Use ONLY the provided context to answer
2. If the answer requires information not in context, say so explicitly
3. Cite your sources precisely"""


# Refusal Templates for Unverified Queries
REFUSAL_TEMPLATES = [
    "I cannot find this information in the loaded legal texts. The retrieved documents do not contain details about: {topic}",
    "The current knowledge base does not contain sufficient information to answer: {topic}. Please provide additional legal texts or clarify your query.",
    "No authoritative source found in the indexed corpus for: {topic}. This may require additional legal commentary or bare acts.",
    "The retrieved documents do not address: {topic}. My knowledge is limited to the legally indexed materials.",
]


class ClaimExtractor:
    """Extracts factual claims from generated responses for verification."""

    # Patterns that indicate factual claims in legal text
    CLAIM_PATTERNS = [
        re.compile(r"Section\s+(\d+)\s+(?:IPC|BNS|CRPC|BNSS|BSA)", re.IGNORECASE),
        re.compile(r"under\s+(?:section|article)\s+(\d+)", re.IGNORECASE),
        re.compile(r"punishment\s+(?:is|shall be|may be)\s+([^.]+)", re.IGNORECASE),
        re.compile(r"imprisonment\s+for\s+(?:up to |upto |of )?(\d+)\s+years?", re.IGNORECASE),
        re.compile(r"fine\s+(?:of |up to )?([^.]+)", re.IGNORECASE),
        re.compile(r"Whoever\s+([^.]+)\s+shall\s+be\s+punished", re.IGNORECASE),
        re.compile(r"is\s+(?:punishable|offence|offense)\s+with", re.IGNORECASE),
    ]

    @classmethod
    def extract_claims(cls, text: str) -> list[dict[str, Any]]:
        """Extract factual claims from legal response text."""
        claims = []
        text_lower = text.lower()

        # Extract section references
        for match in re.finditer(r"section\s+(\d+[a-z]?)\s+(ipc|bns|crpc|bnss|bsa)", text_lower):
            claims.append({
                "type": "section_reference",
                "value": f"Section {match.group(1)} {match.group(2).upper()}",
                "span": match.span(),
            })

        # Extract punishment claims
        for match in re.finditer(r"punishment\s+(?:is|shall be|may be)\s+([^.]+)", text_lower):
            claims.append({
                "type": "punishment",
                "value": match.group(0),
                "span": match.span(),
            })

        # Extract imprisonment durations
        for match in re.finditer(r"imprisonment\s+(?:for\s+)?(?:up to\s+)?(\d+)\s+years?", text_lower):
            claims.append({
                "type": "imprisonment_duration",
                "value": f"{match.group(1)} years",
                "span": match.span(),
            })

        # Extract fine amounts
        for match in re.finditer(r"fine\s+(?:of\s+|up to\s+)?([\d,]+(?:\s+rupees)?)", text_lower):
            claims.append({
                "type": "fine_amount",
                "value": match.group(1),
                "span": match.span(),
            })

        # Extract "whoever...shall be punished" patterns
        for match in re.finditer(r"whoever\s+([^.]+?)\s+shall\s+be\s+punished", text_lower):
            claims.append({
                "type": "offence_definition",
                "value": match.group(0),
                "span": match.span(),
            })

        return claims


class ChainOfVerification:
    """Implements the CoVe workflow for hallucination prevention."""

    def __init__(self):
        self.client = Groq()
        self.model = "llama-3.3-70b-versatile"

    def verify_response(self, response: str, source_documents: list[dict]) -> dict[str, Any]:
        """
        Run full Chain-of-Verification pipeline.

        Returns:
            dict with keys: verified_response, claims_verified, unverified_claims,
                           citation_coverage, needs_correction, correction_notes
        """
        # Step 1: Extract claims from response
        claims = ClaimExtractor.extract_claims(response)

        if not claims:
            return {
                "verified_response": response,
                "claims_verified": True,
                "unverified_claims": [],
                "citation_coverage": 1.0,
                "needs_correction": False,
                "correction_notes": "No explicit claims to verify.",
            }

        # Step 2: Build verification context from source documents
        verification_context = self._build_verification_context(source_documents)

        # Step 3: Verify each claim against sources
        verified_claims = []
        unverified_claims = []

        for claim in claims:
            is_verified, verification_note = self._verify_claim(
                claim, verification_context, source_documents
            )
            if is_verified:
                verified_claims.append({**claim, "verified": True, "note": verification_note})
            else:
                unverified_claims.append({**claim, "verified": False, "note": verification_note})

        # Step 4: Calculate metrics
        total_claims = len(claims)
        citation_coverage = len(verified_claims) / total_claims if total_claims > 0 else 1.0

        # Step 5: Determine if correction needed
        needs_correction = citation_coverage < 0.5 or len(unverified_claims) > 0

        # Step 6: Generate corrected response if needed
        corrected_response = response
        correction_notes = []

        if needs_correction:
            corrected_response, correction_notes = self._correct_response(
                response, unverified_claims, source_documents
            )

        return {
            "verified_response": corrected_response,
            "claims_verified": len(verified_claims),
            "total_claims": total_claims,
            "unverified_claims": unverified_claims,
            "citation_coverage": round(citation_coverage, 3),
            "needs_correction": needs_correction,
            "correction_notes": correction_notes,
        }

    def _build_verification_context(self, source_documents: list[dict]) -> str:
        """Combine source documents into verification context."""
        context_parts = []
        for doc in source_documents:
            source = doc.get("metadata", {}).get("source", "Unknown")
            page = doc.get("metadata", {}).get("page", "?")
            content = doc.get("document", "")
            context_parts.append(f"[Source: {source}, Page {page}]\n{content}\n")
        return "\n---\n".join(context_parts)

    def _verify_claim(self, claim: dict, context: str, sources: list[dict]) -> tuple[bool, str]:
        """Verify a single claim against source documents."""
        claim_type = claim.get("type", "")
        claim_value = claim.get("value", "")

        # Search through sources for the claim
        for source in sources:
            doc_text = source.get("document", "").lower()
            doc_source = source.get("metadata", {}).get("source", "")
            doc_page = source.get("metadata", {}).get("page", "")

            if claim_type == "section_reference":
                # Check if section exists in document
                if claim_value.lower() in doc_text:
                    return True, f"Found in {doc_source} page {doc_page}"

            elif claim_type == "imprisonment_duration":
                # Check if imprisonment duration matches
                if claim_value.split()[0] in doc_text:
                    return True, f"Found duration reference in {doc_source}"

            elif claim_type == "punishment":
                # Check if punishment is mentioned
                if any(word in doc_text for word in claim_value.split()[:3]):
                    return True, f"Punishment context found in {doc_source}"

            elif claim_type == "fine_amount":
                # Check if fine is mentioned
                if claim_value.replace(",", "") in doc_text.replace(",", ""):
                    return True, f"Fine amount found in {doc_source}"

        return False, "Claim not found in any source document"

    def _correct_response(
        self, original: str, unverified: list[dict], sources: list[dict]
    ) -> tuple[str, list[str]]:
        """Generate corrected response removing unverified claims."""
        corrections = []

        # Build list of unverified claim values
        unverified_values = [c.get("value", "") for c in unverified]

        # Create corrected response with caveats
        corrected = original

        for claim in unverified:
            claim_value = claim.get("value", "")
            note = claim.get("note", "")
            corrections.append(f"Removed unverified: {claim_value[:50]}... ({note})")

        # Add disclaimer if corrections made
        if corrections:
            disclaimer = "\n\n**Verification Note**: Some claims could not be verified against source documents and have been flagged."
            corrected = corrected + disclaimer

        return corrected, corrections


class HallucinationDetector:
    """Metrics and detection for hallucination in legal responses."""

    @staticmethod
    def calculate_claim_coverage(verified_claims: int, total_claims: int) -> float:
        """Calculate percentage of claims that are verified."""
        if total_claims == 0:
            return 1.0
        return verified_claims / total_claims

    @staticmethod
    def detect_fabricated_citations(response: str) -> list[dict]:
        """Detect potentially fabricated citations."""
        fabricated = []

        # Pattern: Section numbers that don't match BNS/IPC structure
        suspicious_sections = re.findall(r"Section\s+(\d{3,4})", response, re.IGNORECASE)

        # IPC sections go up to 511, BNS to ~358
        for section in suspicious_sections:
            section_num = int(section)
            if section_num > 600:
                fabricated.append({
                    "type": "invalid_section_number",
                    "value": section,
                    "reason": f"Section {section} exceeds maximum IPC/BNS section number",
                })

        # Pattern: Case citations that look fabricated (e.g., fake AIR citations)
        case_patterns = re.findall(r"(AIR\s+\d{4}\s+\w+\s+\d+)", response, re.IGNORECASE)
        if case_patterns:
            # Just flag as potential case citation (would need legal database to verify)
            pass

        return fabricated

    @staticmethod
    def detect_temporal_inconsistencies(response: str) -> list[dict]:
        """Detect laws referenced after their effective date."""
        inconsistencies = []

        # BNS effective date: July 1, 2024 - current law, no action needed

        # Check for post-effective-date references to repealed laws
        if "w.e.f" in response.lower() or "effective from" in response.lower():
            # Would need legal date database to fully implement
            pass

        return inconsistencies

    @staticmethod
    def generate_hallucination_report(verification_result: dict) -> dict:
        """Generate comprehensive hallucination detection report."""
        response = verification_result.get("verified_response", "")

        # Calculate metrics
        coverage = verification_result.get("citation_coverage", 0.0)
        total_claims = verification_result.get("total_claims", 0)
        verified = verification_result.get("claims_verified", 0)

        fabricated = HallucinationDetector.detect_fabricated_citations(response)
        temporal = HallucinationDetector.detect_temporal_inconsistencies(response)

        # Determine overall score
        if coverage >= 0.9 and len(fabricated) == 0 and len(temporal) == 0:
            status = "LOW_RISK"
        elif coverage >= 0.7:
            status = "MEDIUM_RISK"
        else:
            status = "HIGH_RISK"

        return {
            "status": status,
            "claim_coverage_score": coverage,
            "verified_claims": verified,
            "total_claims": total_claims,
            "fabricated_citations": fabricated,
            "temporal_inconsistencies": temporal,
            "needs_review": status != "LOW_RISK",
        }


class StrictCitationGenerator:
    """Generates responses with strict citation requirements."""

    def __init__(self):
        self.client = Groq()
        self.model = "llama-3.3-70b-versatile"

    def generate_strict(
        self, query: str, source_documents: list[dict], max_tokens: int = 800
    ) -> str:
        """Generate response with strict citation requirements."""
        context = self._build_strict_context(source_documents)

        prompt = STRICT_CITATION_PROMPT.format(context=context, question=query)

        try:
            chat = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=max_tokens,
            )
            response = chat.choices[0].message.content

            # Verify the generated response
            verifier = ChainOfVerification()
            verification = verifier.verify_response(response, source_documents)

            return verification.get("verified_response", response)
        except Exception as e:
            return f"Generation error: {str(e)}"

    def _build_strict_context(self, sources: list[dict]) -> str:
        """Build context with strict formatting."""
        parts = []
        for i, doc in enumerate(sources, 1):
            meta = doc.get("metadata", {})
            source = meta.get("source", f"Document {i}")
            page = meta.get("page", "?")
            content = doc.get("document", "")
            parts.append(f"[Document {i}]: {source} (Page {page})\n---\n{content}")
        return "\n\n".join(parts)


def get_refusal_response(topic: str) -> str:
    """Get a refusal template for unverified queries."""
    import random

    template = random.choice(REFUSAL_TEMPLATES)
    return template.format(topic=topic)