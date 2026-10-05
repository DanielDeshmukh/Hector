"""Round 5 fail-first tests: claim-grounding verifier hardening.

(a) wrong penalty term must not verify against a different penalty chunk
(b) fine amount prefix (50 vs 5000) must not verify
(c) mixed abstention sentence: assertive clause still extracted/checked
(d) broad section extractor forms: "of the BNS", "(1) BNS", "Section: N",
    bare "Section N states..."
(e) word-boundary matching for section / article / § references
(f) calculate_claim_coverage(0, 0) is None, never 1.0
(g) legal-text uses of contextual markers ("does not include") are claims,
    not abstentions
"""

import sys
from pathlib import Path

import pytest

_PROJECT = Path(__file__).resolve().parents[1]
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from core.verifier import (  # noqa: E402
    ClaimExtractor,
    ChainOfVerification,
    HallucinationDetector,
    is_abstention_answer,
    is_abstention_sentence,
)

MIXED = (
    "The sources do not contain the fine, but Section 999 BNS "
    "punishes it with 50 years."
)


# ---------------------------------------------------------------------------
# (a) Wrong penalty must not verify
# ---------------------------------------------------------------------------


def test_wrong_penalty_term_not_verified():
    verifier = ChainOfVerification()
    response = "Section 302 BNS: the punishment is imprisonment for 2 years."
    sources = [
        {
            "document": (
                "Section 302 BNS. Whoever commits murder shall be punished "
                "with death or imprisonment for life."
            ),
            "metadata": {"source": "bns.pdf", "page": 9},
        }
    ]

    result = verifier.verify_response(response, sources)

    duration_bad = [
        c
        for c in result["unverified_claims"]
        if c["type"] == "imprisonment_duration"
    ]
    assert duration_bad, (
        "claim 'imprisonment for 2 years' must NOT verify against a chunk "
        f"whose penalty is death/life; got {result['unverified_claims']}"
    )
    punishment_bad = [
        c for c in result["unverified_claims"] if c["type"] == "punishment"
    ]
    assert punishment_bad, (
        "punishment claim with a 2-year term must NOT verify against a "
        f"death/life chunk; got {result['unverified_claims']}"
    )


# ---------------------------------------------------------------------------
# (b) Fine prefix must not verify
# ---------------------------------------------------------------------------


def test_fine_prefix_amount_not_verified():
    verifier = ChainOfVerification()
    response = "Under Section 43 BNS the fine of 50 is prescribed."
    sources = [
        {
            "document": (
                "Section 43 BNS. Every person convicted of this offence "
                "shall pay a fine which may extend to 5000 rupees."
            ),
            "metadata": {"source": "bns.pdf", "page": 4},
        }
    ]

    result = verifier.verify_response(response, sources)

    fine_bad = [
        c for c in result["unverified_claims"] if c["type"] == "fine_amount"
    ]
    assert fine_bad, (
        "claim 'fine of 50' must NOT verify against a chunk that only "
        f"mentions 5000; got {result['unverified_claims']}"
    )


# ---------------------------------------------------------------------------
# (c) Mixed abstention sentence: assertive clause still checked
# ---------------------------------------------------------------------------


def test_mixed_sentence_claims_extracted_and_status_not_na():
    verifier = ChainOfVerification()
    sources = [
        {
            "document": "Section 100 BNS. General provisions of the Sanhita.",
            "metadata": {"source": "bns.pdf", "page": 1},
        }
    ]

    claims = ClaimExtractor.extract_claims(MIXED)
    section_claims = [
        c
        for c in claims
        if c["type"] == "section_reference" and "999" in c["value"]
    ]
    assert section_claims, f"Section 999 claim must be extracted: {claims}"
    duration_claims = [
        c
        for c in claims
        if c["type"] == "imprisonment_duration" and c["value"] == "50 years"
    ]
    assert duration_claims, f"50-years claim must be extracted: {claims}"

    result = verifier.verify_response(MIXED, sources)
    assert result["claims_total"] >= 2, result
    assert result["status"] != "NOT_APPLICABLE", result
    assert result["citation_coverage"] is not None, result


def test_mixed_sentence_is_not_a_whole_answer_abstention():
    assert not is_abstention_sentence(MIXED)
    assert not is_abstention_answer(MIXED)


def test_pure_refusal_still_not_applicable():
    verifier = ChainOfVerification()
    result = verifier.verify_response(
        "I cannot find this information in the loaded legal texts.", []
    )
    assert result["status"] == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# (d) Broad section extractor forms
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Section 103 of the BNS deals with murder.", "Section 103 BNS"),
        ("Section 103(1) BNS prescribes the penalty.", "Section 103 BNS"),
        ("Section: 103 BNS applies to culpable homicide.", "Section 103 BNS"),
        ("Section 103 states that murder is punishable.", "Section 103"),
    ],
)
def test_broad_section_extractor_forms(text, expected):
    claims = ClaimExtractor.extract_claims(text)
    section_values = [
        c["value"] for c in claims if c["type"] == "section_reference"
    ]
    assert expected in section_values, (
        f"expected section_reference {expected!r} from {text!r}; "
        f"got {section_values} (all claims: {claims})"
    )


# ---------------------------------------------------------------------------
# (e) Word-boundary matching
# ---------------------------------------------------------------------------


def test_section_number_boundary_not_prefix_match():
    verifier = ChainOfVerification()
    response = "Under \u00a7 5, appeals must be filed within ninety days."
    sources = [
        {
            "document": (
                "Section 50 of the Act provides for appeals from "
                "appellate decrees."
            ),
            "metadata": {"source": "act.pdf", "page": 3},
        }
    ]

    result = verifier.verify_response(response, sources)

    assert result["claims_total"] >= 1, result
    assert result["claims_unsupported"] == 1, (
        "Section 5 must not verify against a chunk that only has "
        f"Section 50; got {result}"
    )


def test_article_number_boundary_not_prefix_match():
    verifier = ChainOfVerification()
    response = (
        "Article 19 guarantees freedom of speech and expression."
    )
    sources = [
        {
            "document": (
                "Article 190 of the Constitution deals with legislative "
                "powers of Parliament."
            ),
            "metadata": {"source": "constitution.pdf", "page": 7},
        }
    ]

    result = verifier.verify_response(response, sources)

    assert result["claims_total"] >= 1, result
    assert result["claims_unsupported"] == 1, (
        "Article 19 must not verify against Article 190; got "
        f"{result['unverified_claims']}"
    )


def test_bare_section_number_extracted_and_boundary_checked():
    verifier = ChainOfVerification()
    response = "Section 5 states that limitation applies to suits."
    sources = [
        {
            "document": (
                "Section 50 of the Limitation Act empowers the court "
                "to extend time."
            ),
            "metadata": {"source": "limitation_act.pdf", "page": 1},
        }
    ]

    result = verifier.verify_response(response, sources)

    assert result["claims_total"] >= 1, (
        f"bare 'Section 5' must be extracted; got {result}"
    )
    assert result["claims_unsupported"] == 1, (
        "Section 5 must not verify against Section 50; got "
        f"{result['unverified_claims']}"
    )


def test_section_symbol_source_form_matches():
    verifier = ChainOfVerification()
    response = "Under \u00a7 7, appeals lie to the District Judge."
    sources = [
        {
            "document": (
                "\u00a7 7 of the Act provides that appeals lie to the "
                "District Judge."
            ),
            "metadata": {"source": "act.pdf", "page": 2},
        }
    ]

    result = verifier.verify_response(response, sources)

    assert result["claims_total"] >= 1, result
    assert result["claims_supported"] >= 1, (
        "a claim for Section 7 must verify against a source written as "
        f"'§ 7'; got {result}"
    )


# ---------------------------------------------------------------------------
# (f) Zero-claim coverage
# ---------------------------------------------------------------------------


def test_zero_claim_coverage_is_none_not_one():
    assert HallucinationDetector.calculate_claim_coverage(0, 0) is None


# ---------------------------------------------------------------------------
# (g) Contextual markers in normal legal text
# ---------------------------------------------------------------------------


def test_legal_text_does_not_include_is_not_abstention():
    verifier = ChainOfVerification()
    response = "Section 106 does not include abetment in its provisions."
    sources = [
        {
            "document": (
                "Section 106 BNS. A person who abets the commission of "
                "an offence is punishable with imprisonment of two years."
            ),
            "metadata": {"source": "bns.pdf", "page": 12},
        }
    ]

    claims = ClaimExtractor.extract_claims(response)
    assert any(
        c["type"] == "section_reference" and "106" in c["value"]
        for c in claims
    ), f"legal-text 'does not include' sentence must keep its claim: {claims}"

    result = verifier.verify_response(response, sources)
    assert result["claims_total"] >= 1, result
    assert result["status"] != "NOT_APPLICABLE", result
