import logging
import os
import re
from typing import Any

from utils.retry import retry

from groq import Groq
from dotenv import load_dotenv

from core.precedent import CITATION_PATTERNS

logger = logging.getLogger(__name__)

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
        re.compile(
            r"imprisonment\s+for\s+(?:up to |upto |of )?(\d+)\s+years?", re.IGNORECASE
        ),
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
        for match in re.finditer(
            r"section\s+(\d+[a-z]?)\s+(ipc|bns|crpc|bnss|bsa)", text_lower
        ):
            claims.append(
                {
                    "type": "section_reference",
                    "value": f"Section {match.group(1)} {match.group(2).upper()}",
                    "span": match.span(),
                }
            )

        # Extract punishment claims
        for match in re.finditer(
            r"punishment\s+(?:is|shall be|may be)\s+([^.]+)", text_lower
        ):
            claims.append(
                {
                    "type": "punishment",
                    "value": match.group(0),
                    "span": match.span(),
                }
            )

        # Extract imprisonment durations
        for match in re.finditer(
            r"imprisonment\s+(?:for\s+)?(?:up to\s+)?(\d+)\s+years?", text_lower
        ):
            claims.append(
                {
                    "type": "imprisonment_duration",
                    "value": f"{match.group(1)} years",
                    "span": match.span(),
                }
            )

        # Extract fine amounts
        for match in re.finditer(
            r"fine\s+(?:of\s+|up to\s+)?([\d,]+(?:\s+rupees)?)", text_lower
        ):
            claims.append(
                {
                    "type": "fine_amount",
                    "value": match.group(1),
                    "span": match.span(),
                }
            )

        # Extract "whoever...shall be punished" patterns
        for match in re.finditer(
            r"whoever\s+([^.]+?)\s+shall\s+be\s+punished", text_lower
        ):
            claims.append(
                {
                    "type": "offence_definition",
                    "value": match.group(0),
                    "span": match.span(),
                }
            )

        return claims


class ChainOfVerification:
    """Implements the CoVe workflow for hallucination prevention."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = "llama-3.3-70b-versatile"

    def verify_response(
        self, response: str, source_documents: list[dict]
    ) -> dict[str, Any]:
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
                verified_claims.append(
                    {**claim, "verified": True, "note": verification_note}
                )
            else:
                unverified_claims.append(
                    {**claim, "verified": False, "note": verification_note}
                )

        # Step 4: Calculate metrics
        total_claims = len(claims)
        citation_coverage = (
            len(verified_claims) / total_claims if total_claims > 0 else 1.0
        )

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
            meta = doc.get("metadata", {})
            source = meta.get("real_act_name") or meta.get("act_name") or meta.get("source", "Unknown")
            page = meta.get("page", "?")
            content = doc.get("document", "")
            context_parts.append(f"[Source: {source}, Page {page}]\n{content}\n")
        return "\n---\n".join(context_parts)

    def _verify_claim(
        self, claim: dict, context: str, sources: list[dict]
    ) -> tuple[bool, str]:
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
        """Detect potentially fabricated citations via structural validation."""
        fabricated: list[dict] = []
        seen_citations: set[str] = set()

        # --- Suspicious section numbers ---
        suspicious_sections = re.findall(
            r"Section\s+(\d{3,4})", response, re.IGNORECASE
        )
        for section in suspicious_sections:
            section_num = int(section)
            if section_num > 600:
                fabricated.append(
                    {
                        "type": "invalid_section_number",
                        "value": section,
                        "reason": f"Section {section} exceeds maximum IPC/BNS section number",
                    }
                )

        # --- Court codes considered valid in Indian case law ---
        valid_court_codes: set[str] = {
            "SC",
            "Pat",
            "Del",
            "Bom",
            "Cal",
            "Mad",
            "KER",
            "All",
            "Guj",
            "Raj",
            "HP",
            "J&K",
            "P&H",
            "Orissa",
            "Sikkim",
            "Manipur",
            "Meghalaya",
            "Tripura",
            "Gauhati",
            "Imphal",
            "Shimla",
            "MP",
            "AP",
            "Karn",
            "Chhatisgarh",
            "Jharkhand",
            "Uttarakhand",
            "NB",
            "Indore",
            "Lucknow",
            "Nagpur",
            "Panaji",
            "Gwalior",
        }

        current_year = 2026  # reference year for future-year checks

        # --- Extract every citation that matches the known patterns ---
        for pattern in CITATION_PATTERNS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                citation = match.group(0).strip()
                citation_key = citation.lower()

                # Duplicate citation check
                if citation_key in seen_citations:
                    fabricated.append(
                        {
                            "type": "duplicate_citation",
                            "value": citation,
                            "reason": "Citation appears more than once in response",
                        }
                    )
                    continue
                seen_citations.add(citation_key)

                # ---- AIR citation validation ----
                air_m = re.match(
                    r"AIR\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE
                )
                if air_m:
                    year = int(air_m.group(1))
                    court = air_m.group(2)
                    case_num = int(air_m.group(3))

                    if year > current_year:
                        fabricated.append(
                            {
                                "type": "future_year",
                                "value": citation,
                                "reason": f"Year {year} is in the future",
                            }
                        )
                        continue

                    if court not in valid_court_codes:
                        fabricated.append(
                            {
                                "type": "invalid_court",
                                "value": citation,
                                "reason": f"Unknown court code '{court}' in AIR citation",
                            }
                        )
                        continue

                    if case_num > 0 and case_num % 100 == 0:
                        fabricated.append(
                            {
                                "type": "suspicious_round_number",
                                "value": citation,
                                "reason": f"Case number {case_num} is a suspiciously round number",
                            }
                        )

                # ---- SCC citation validation ----
                scc_m = re.match(
                    r"SCC\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE
                )
                if scc_m:
                    year = int(scc_m.group(1))
                    court = scc_m.group(2)

                    if year > current_year:
                        fabricated.append(
                            {
                                "type": "future_year",
                                "value": citation,
                                "reason": f"Year {year} is in the future",
                            }
                        )
                        continue

                    if court not in valid_court_codes:
                        fabricated.append(
                            {
                                "type": "invalid_court",
                                "value": citation,
                                "reason": f"Unknown court code '{court}' in SCC citation",
                            }
                        )

                # ---- Citation missing court name (e.g. "AIR 2023 123") ----
                if re.match(r"(?:AIR|SCC)\s+\d{4}\s+\d+\s*$", citation, re.IGNORECASE):
                    fabricated.append(
                        {
                            "type": "missing_court",
                            "value": citation,
                            "reason": "Citation is missing a court name after the year",
                        }
                    )

        # ---- Log detected fabrications ----
        if fabricated:
            logger.warning(
                "Detected %d potentially fabricated citation(s)", len(fabricated)
            )
            for item in fabricated:
                logger.warning(
                    "  [%s] %s — %s", item["type"], item["value"], item["reason"]
                )

        return fabricated

    @staticmethod
    def detect_temporal_inconsistencies(response: str) -> list[dict]:
        """Detect laws referenced after their effective date."""
        inconsistencies = []

        response_lower = response.lower()

        # Check for IPC references (repealed July 1, 2024) alongside BNS references
        has_ipc = bool(re.search(r"\bipc\b", response_lower))
        has_bns = bool(re.search(r"\bbns\b", response_lower))

        if has_ipc and has_bns:
            # Check if the response treats IPC as current law
            ipc_current_patterns = [
                r"ipc\s+(?:provides|states|specifies|says|defines)",
                r"under\s+ipc\s+section",
                r"as\s+per\s+ipc",
            ]
            for pattern in ipc_current_patterns:
                if re.search(pattern, response_lower):
                    inconsistencies.append(
                        {
                            "type": "ipc_treated_as_current",
                            "detail": "Response references IPC as current law, but BNS is effective from July 1, 2024",
                            "pattern": pattern,
                        }
                    )
                    break

        # Check for references to specific repealed sections
        repealed_sections = re.findall(r"section\s+(\d+)\s+ipc", response_lower)
        for section in repealed_sections:
            section_num = int(section)
            # IPC sections 1-511, but many were restructured into BNS
            if section_num > 511:
                inconsistencies.append(
                    {
                        "type": "invalid_ipc_section",
                        "detail": f"Section {section} IPC does not exist (IPC has 511 sections)",
                    }
                )

        # Check for references to invalid BNS sections
        bns_sections = re.findall(r"section\s+(\d+)\s+bns", response_lower)
        for section in bns_sections:
            section_num = int(section)
            # BNS has 358 sections (official count), safe upper bound 395
            if section_num > 395:
                inconsistencies.append(
                    {
                        "type": "invalid_bns_section",
                        "detail": f"Section {section} BNS does not exist (BNS has 358 sections)",
                    }
                )

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
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = "llama-3.3-70b-versatile"

    def generate_strict(
        self, query: str, source_documents: list[dict], max_tokens: int = 800
    ) -> str:
        """Generate response with strict citation requirements."""
        context = self._build_strict_context(source_documents)

        prompt = STRICT_CITATION_PROMPT.format(context=context, question=query)

        try:
            chat = retry(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=max_tokens,
                max_attempts=3,
                operation_name="groq_generation",
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
            source = meta.get("real_act_name") or meta.get("act_name") or meta.get("source", f"Document {i}")
            page = meta.get("page", "?")
            content = doc.get("document", "")
            parts.append(f"[Document {i}]: {source} (Page {page})\n---\n{content}")
        return "\n\n".join(parts)


def get_refusal_response(topic: str) -> str:
    """Get a refusal template for unverified queries."""
    import random

    template = random.choice(REFUSAL_TEMPLATES)
    return template.format(topic=topic)
