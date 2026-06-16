from core.router import HectorRouter
from data.hybrid_retriever import HectorHybridRetriever

# Optional: Only import verifier if available (graceful degradation)
try:
    from core.verifier import ChainOfVerification

    VERIFIER_AVAILABLE = True
except ImportError:
    VERIFIER_AVAILABLE = False


class HectorOrchestrator:
    def __init__(self, enable_verification=True):
        self.router = HectorRouter()
        self.retriever = HectorHybridRetriever()
        self.enable_verification = enable_verification and VERIFIER_AVAILABLE
        self.verifier = ChainOfVerification() if VERIFIER_AVAILABLE else None

    def execute(self, query):
        """
        The Master Execution Loop.
        1. Route Intent
        2. Normalize Legal Queries (IPC -> BNS)
        3. Retrieve/Generate Strategy
        4. Verify (if enabled)
        """
        # Step 1: Routing & Diagnostic
        intent = self.router.get_route(query)
        if not isinstance(intent, dict):
            intent = self.router._fallback_intent()
        route = intent.get("route", "GENERAL")

        # Step 2: Legal Normalization (only for research)
        normalized_query = query
        mappings = []
        if route == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(query)

        # Step 3: Intelligence Generation
        try:
            response, sources = self._generate_strategic_response(
                route, normalized_query, intent, mappings
            )
        except Exception as e:
            return f"Strategic failure: {str(e)}"

        # Step 4: Verification for Legal Research
        if route == "LEGAL_RESEARCH" and self.enable_verification and sources:
            verification = self.verifier.verify_response(response, sources)

            if verification.get("needs_correction"):
                response = verification.get("verified_response", response)

            # Optionally include verification metrics in response
            coverage = verification.get("citation_coverage", 0)
            if coverage < 0.8:
                verification_note = (
                    f"\n\n[Verification: {coverage:.0%} claims verified]"
                )
                response += verification_note

        return response

    def _generate_strategic_response(self, route, query, intent, mappings=None):
        """Internal logic to fetch either legal data or general scaling advice."""
        hector_msg = intent.get("hector_response", "")
        mappings = mappings or []
        sources = []

        if route == "GENERAL":
            if len(hector_msg) > 5:
                return hector_msg, sources
            return (
                "Tactical pivot required. Provide more specific architecture logs.",
                sources,
            )

        if route == "LEGAL_RESEARCH":
            results = self.retriever.search(query, top_k=5)
            sources = results  # Track sources for verification

            preface = [hector_msg] if hector_msg else []
            if mappings:
                preface.append("Mapped legacy references: " + "; ".join(mappings))
            preface.append(self.retriever.format_results(results))
            return "\n\n".join(preface), sources

        if route == "STRATEGIC_ADVICE":
            if len(hector_msg) > 5:
                return hector_msg, sources
            return (
                "Strategic route selected. State the target outcome, constraints, and leverage points.",
                sources,
            )

        if route == "DOCUMENT_ANALYSIS":
            if len(hector_msg) > 5:
                return hector_msg, sources
            return (
                "Document analysis route selected. Provide the file or OCR payload to continue.",
                sources,
            )

        return (
            "Fallback route engaged. Clarify the objective and I will reclassify.",
            sources,
        )
