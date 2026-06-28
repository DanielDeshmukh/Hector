import time

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
        t0 = time.perf_counter()
        intent = self.router.get_route(query)
        if not isinstance(intent, dict):
            intent = self.router._fallback_intent()
        route = intent.get("route", "GENERAL")
        route_ms = (time.perf_counter() - t0) * 1000

        # Step 2: Legal Normalization (only for research)
        t1 = time.perf_counter()
        normalized_query = query
        mappings = []
        if route == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(query)
        normalize_ms = (time.perf_counter() - t1) * 1000

        # Step 3: Intelligence Generation
        t2 = time.perf_counter()
        try:
            response, sources = self._generate_strategic_response(
                route, normalized_query, intent, mappings
            )
        except Exception as e:
            return f"Strategic failure: {str(e)}"
        generate_ms = (time.perf_counter() - t2) * 1000

        # Step 4: Verification for Legal Research
        verify_ms = 0
        if route == "LEGAL_RESEARCH" and self.enable_verification and sources:
            t3 = time.perf_counter()
            verification = self.verifier.verify_response(response, sources)
            verify_ms = (time.perf_counter() - t3) * 1000

            if verification.get("needs_correction"):
                response = verification.get("verified_response", response)

            # Optionally include verification metrics in response
            coverage = verification.get("citation_coverage", 0)
            if coverage < 0.8:
                verification_note = (
                    f"\n\n[Verification: {coverage:.0%} claims verified]"
                )
                response += verification_note

        total_ms = (time.perf_counter() - t0) * 1000

        # Attach timing metadata (used by benchmark and API response)
        self._last_timing = {
            "route_ms": round(route_ms, 1),
            "normalize_ms": round(normalize_ms, 1),
            "generate_ms": round(generate_ms, 1),
            "verify_ms": round(verify_ms, 1),
            "total_ms": round(total_ms, 1),
        }

        return response

    def get_last_timing(self) -> dict:
        """Return timing from the last execute() call."""
        return getattr(self, "_last_timing", {})

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
