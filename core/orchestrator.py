from core.router import HectorRouter
# Assuming you have these or similar in your project
# from core.retriever import HybridRetriever 

class HectorOrchestrator:
    def __init__(self):
        self.router = HectorRouter()
        # self.retriever = HybridRetriever()

    def execute(self, query):
        """
        The Master Execution Loop.
        1. Route Intent
        2. Normalize Legal Queries (IPC -> BNS)
        3. Retrieve/Generate Strategy
        """
        # Step 1: Routing & Diagnostic
        intent = self.router.get_route(query)
        if not isinstance(intent, dict):
            intent = self.router._fallback_intent()
        route = intent.get("route", "GENERAL")
        
        # Step 2: Legal Normalization (only for research)
        normalized_query = query
        if route == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(query)

        # Step 3: Intelligence Generation
        # This is where the 'True' error usually happens. 
        # Ensure we return a STRING, not a success status.
        try:
            response = self._generate_strategic_response(route, normalized_query, intent)
            return response
        except Exception as e:
            return f"Strategic failure: {str(e)}"

    def _generate_strategic_response(self, route, query, intent):
        """Internal logic to fetch either legal data or general scaling advice."""
        hector_msg = intent.get("hector_response", "")
        
        if route == "GENERAL":
            if len(hector_msg) > 5:
                return hector_msg
            return "Tactical pivot required. Provide more specific architecture logs."

        if route == "LEGAL_RESEARCH":
            return "The archives are empty on this query. We need to ingest the relevant Gazette files."

        if route == "STRATEGIC_ADVICE":
            if len(hector_msg) > 5:
                return hector_msg
            return "Strategic route selected. State the target outcome, constraints, and leverage points."

        if route == "DOCUMENT_ANALYSIS":
            if len(hector_msg) > 5:
                return hector_msg
            return "Document analysis route selected. Provide the file or OCR payload to continue."

        return "Fallback route engaged. Clarify the objective and I will reclassify."
