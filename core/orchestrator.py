"""
HECTOR Orchestrator - Master Execution Loop

Integrates all retrieval pipeline components:
1. Query Parser (Phase A) - Extract legal entities
2. Embedding Router (Phase B) - Intent classification via cosine similarity
3. Query Expansion (Phase C) - Synonym expansion for better recall
4. Entity Re-ranking (Phase D) - Boost results by entity match

Pipeline flow:
  Query → Parse Entities → Route Intent → Expand Query → Search → Re-rank → Response
"""

import time

from core.router import HectorRouter
from core.query_parser import LegalQueryParser, get_parser
from core.embedding_router import EmbeddingRouter, get_embedding_router
from core.query_expander import QueryExpander, get_query_expander
from core.entity_reranker import EntityReranker, get_entity_reranker
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

        # Pipeline components (lazy-loaded)
        self._query_parser = None
        self._embedding_router = None
        self._query_expander = None
        self._entity_reranker = None
        self._response_generator = None

    @property
    def query_parser(self) -> LegalQueryParser:
        if self._query_parser is None:
            self._query_parser = get_parser()
        return self._query_parser

    @property
    def embedding_router(self) -> EmbeddingRouter:
        if self._embedding_router is None:
            self._embedding_router = get_embedding_router()
        return self._embedding_router

    @property
    def query_expander(self) -> QueryExpander:
        if self._query_expander is None:
            self._query_expander = get_query_expander()
        return self._query_expander

    @property
    def entity_reranker(self) -> EntityReranker:
        if self._entity_reranker is None:
            self._entity_reranker = get_entity_reranker()
        return self._entity_reranker

    @property
    def response_generator(self):
        if self._response_generator is None:
            from core.response_generator import ContextualResponseGenerator
            self._response_generator = ContextualResponseGenerator(self.retriever)
        return self._response_generator

    def execute(self, query):
        """
        The Master Execution Loop with full retrieval pipeline.
        1. Parse legal entities from query (Phase A)
        2. Route intent with rule-based + embedding backup (Phase B)
        3. Normalize legal queries (IPC -> BNS)
        4. Expand query with synonyms (Phase C)
        5. Retrieve with hybrid search
        6. Re-rank by entity matches (Phase D)
        7. Generate response
        8. Verify (if enabled)
        """
        # Step 1: Parse entities (Phase A)
        t_parse = time.perf_counter()
        entities = self.query_parser.parse(query)
        entity_dict = entities.to_dict()
        parse_ms = (time.perf_counter() - t_parse) * 1000

        # Step 2: Route intent
        t_route = time.perf_counter()
        intent = self.router.get_route(query)
        if not isinstance(intent, dict):
            intent = self.router._fallback_intent()
        route = intent.get("route", "GENERAL")
        confidence = intent.get("confidence", 0.0)

        # Phase B: If rule-based confidence is low, try embedding router
        if confidence < 0.7:
            embedding_result = self.embedding_router.route(query)
            if embedding_result:
                embed_route, embed_confidence = embedding_result
                # Use embedding route if it's more confident
                if embed_confidence > confidence:
                    route = embed_route
                    confidence = embed_confidence

        # Phase A: Use parser hint if available and no strong route yet
        if confidence < 0.7:
            parser_hint = self.query_parser.get_route_hint(entities)
            if parser_hint:
                route = parser_hint
                confidence = max(confidence, entities.confidence)

        route_ms = (time.perf_counter() - t_route) * 1000

        # Step 3: Legal normalization (IPC -> BNS)
        t_norm = time.perf_counter()
        normalized_query = query
        mappings = []
        if route == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(query)
        normalize_ms = (time.perf_counter() - t_norm) * 1000

        # Step 4: Expand query (Phase C)
        t_expand = time.perf_counter()
        if route == "LEGAL_RESEARCH":
            expanded_query = self.query_expander.expand_with_entities(
                normalized_query, entity_dict
            )
        else:
            expanded_query = normalized_query
        expand_ms = (time.perf_counter() - t_expand) * 1000

        # Step 5-6: Retrieve and re-rank
        t_retrieve = time.perf_counter()
        try:
            response, sources = self._generate_strategic_response(
                route, expanded_query, intent, mappings, entity_dict
            )
        except Exception as e:
            return f"Strategic failure: {str(e)}"
        retrieve_ms = (time.perf_counter() - t_retrieve) * 1000

        # Step 7: Verification for Legal Research
        verify_ms = 0
        if route == "LEGAL_RESEARCH" and self.enable_verification and sources:
            t_verify = time.perf_counter()
            verification = self.verifier.verify_response(response, sources)
            verify_ms = (time.perf_counter() - t_verify) * 1000

            if verification.get("needs_correction"):
                response = verification.get("verified_response", response)

            coverage = verification.get("citation_coverage", 0)
            if coverage < 0.8:
                verification_note = (
                    f"\n\n[Verification: {coverage:.0%} claims verified]"
                )
                response += verification_note

        # Attach timing metadata
        self._last_timing = {
            "parse_ms": round(parse_ms, 1),
            "route_ms": round(route_ms, 1),
            "normalize_ms": round(normalize_ms, 1),
            "expand_ms": round(expand_ms, 1),
            "retrieve_ms": round(retrieve_ms, 1),
            "verify_ms": round(verify_ms, 1),
            "total_ms": round(
                parse_ms
                + route_ms
                + normalize_ms
                + expand_ms
                + retrieve_ms
                + verify_ms,
                1,
            ),
            "entities": entity_dict,
            "route_confidence": round(confidence, 3),
        }

        return response

    def get_last_timing(self) -> dict:
        """Return timing from the last execute() call."""
        return getattr(self, "_last_timing", {})

    def _generate_strategic_response(
        self, route, query, intent, mappings=None, entities=None
    ):
        """Internal logic to fetch either legal data or general scaling advice."""
        hector_msg = intent.get("hector_response", "")
        mappings = mappings or []
        entities = entities or {}
        sources = []

        if route == "GENERAL":
            if len(hector_msg) > 5:
                return hector_msg, sources
            return (
                "Tactical pivot required. Provide more specific architecture logs.",
                sources,
            )

        if route == "LEGAL_RESEARCH":
            results = self.retriever.search(query, top_k=10)

            # Phase D: Re-rank by entity matches
            if results and entities:
                results = self.entity_reranker.rerank(results, entities)

            # Take top 5 after re-ranking
            results = results[:5]
            sources = results

            # Use response generator with LLM synthesis
            try:
                gen_output = self.response_generator.generate(query, results)
                response = gen_output.get("generated_response", "")
                if not response:
                    raise ValueError("empty response")
            except Exception:
                # Fallback to template
                parts = []
                parts.append(f'Legal research query: "{query}"\n')
                if mappings:
                    parts.append("Mapped legacy references: " + "; ".join(mappings))
                if results:
                    parts.append(self.retriever.format_results(results))
                else:
                    parts.append("No grounded legal results found in the indexed corpus.")
                response = "\n\n".join(parts)

            return response, sources

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
