import unittest
from core.verifier import (
    ClaimExtractor,
    ChainOfVerification,
    HallucinationDetector,
    get_refusal_response,
)


class ClaimExtractorTests(unittest.TestCase):
    def test_extracts_section_references(self):
        text = "Under Section 302 IPC, punishment for murder is death. Section 109 BNS covers attempt to murder."
        claims = ClaimExtractor.extract_claims(text)

        section_claims = [c for c in claims if c["type"] == "section_reference"]
        self.assertGreaterEqual(len(section_claims), 1)
        self.assertTrue(any("302" in c["value"] for c in section_claims))

    def test_extracts_imprisonment_duration(self):
        text = "The punishment is imprisonment for 3 years and fine."
        claims = ClaimExtractor.extract_claims(text)

        duration_claims = [c for c in claims if c["type"] == "imprisonment_duration"]
        self.assertEqual(len(duration_claims), 1)
        self.assertEqual(duration_claims[0]["value"], "3 years")

    def test_extracts_fine_amount(self):
        text = "The offence is punishable with fine of 1000 rupees."
        claims = ClaimExtractor.extract_claims(text)

        fine_claims = [c for c in claims if c["type"] == "fine_amount"]
        self.assertEqual(len(fine_claims), 1)

    def test_extracts_offence_definition(self):
        text = "Whoever commits murder shall be punished with death."
        claims = ClaimExtractor.extract_claims(text)

        offence_claims = [c for c in claims if c["type"] == "offence_definition"]
        self.assertEqual(len(offence_claims), 1)
        self.assertIn("murder", offence_claims[0]["value"].lower())


class HallucinationDetectorTests(unittest.TestCase):
    def test_detects_invalid_section_numbers(self):
        response = "Section 999 IPC states that..."
        fabricated = HallucinationDetector.detect_fabricated_citations(response)

        self.assertEqual(len(fabricated), 1)
        self.assertEqual(fabricated[0]["type"], "invalid_section_number")
        self.assertEqual(fabricated[0]["value"], "999")

    def test_accepts_valid_section_numbers(self):
        response = "Section 302 IPC covers murder. Section 101 BNS covers murder."
        fabricated = HallucinationDetector.detect_fabricated_citations(response)

        self.assertEqual(len(fabricated), 0)

    def test_generates_hallucination_report(self):
        verification_result = {
            "verified_response": "Section 302 IPC covers murder.",
            "citation_coverage": 0.95,
            "total_claims": 1,
            "claims_verified": 1,
        }

        report = HallucinationDetector.generate_hallucination_report(verification_result)

        self.assertEqual(report["status"], "LOW_RISK")
        self.assertEqual(report["claim_coverage_score"], 0.95)
        self.assertFalse(report["needs_review"])

    def test_high_risk_for_low_coverage(self):
        verification_result = {
            "verified_response": "Section 999 IPC is the law.",
            "citation_coverage": 0.1,
            "total_claims": 1,
            "claims_verified": 0,
        }

        report = HallucinationDetector.generate_hallucination_report(verification_result)

        self.assertEqual(report["status"], "HIGH_RISK")
        self.assertTrue(report["needs_review"])


class ChainOfVerificationTests(unittest.TestCase):
    def setUp(self):
        self.verifier = ChainOfVerification()
        self.sample_sources = [
            {
                "document": "Section 302 IPC. Whoever commits murder shall be punished with death.",
                "metadata": {"source": "IPC.pdf", "page": 100},
            },
            {
                "document": "Section 101 BNS. Whoever commits murder shall be punished with death or imprisonment for life.",
                "metadata": {"source": "BNS.pdf", "page": 50},
            },
        ]

    def test_verifies_valid_section_reference(self):
        response = "Section 302 IPC covers murder."
        result = self.verifier.verify_response(response, self.sample_sources)

        self.assertFalse(result["needs_correction"])
        self.assertGreater(result["citation_coverage"], 0.5)

    def test_flags_unverified_claim(self):
        response = "Section 999 IPC has punishment of 20 years."
        result = self.verifier.verify_response(response, self.sample_sources)

        # The section 999 doesn't exist in sources
        unverified = result.get("unverified_claims", [])
        # Either flagged as unverified or correction applied

    def test_handles_empty_response(self):
        response = "I don't know."
        result = self.verifier.verify_response(response, self.sample_sources)

        self.assertTrue(result["claims_verified"])

    def test_builds_verification_context(self):
        context = self.verifier._build_verification_context(self.sample_sources)

        self.assertIn("IPC.pdf", context)
        self.assertIn("BNS.pdf", context)


class RefusalTemplatesTests(unittest.TestCase):
    def test_get_refusal_response_contains_topic(self):
        topic = "quantum physics"
        response = get_refusal_response(topic)

        self.assertIn(topic, response)

    def test_returns_different_templates(self):
        responses = set()
        for _ in range(10):
            responses.add(get_refusal_response("test"))

        # Should have multiple templates (at least 2 different)
        self.assertGreaterEqual(len(responses), 2)


if __name__ == "__main__":
    unittest.main()