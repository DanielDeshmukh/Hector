"""
Contextual Response Generator for HECTOR.
Generates legally accurate, contextually rich responses with proper citations.
"""

from __future__ import annotations
from dataclasses import dataclass
import logging
import os
import re
from typing import TYPE_CHECKING

from core.verifier import is_abstention_answer

logger = logging.getLogger("hector.response_generator")

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever

# ── Act registry: maps keywords/aliases → (full_name, abbreviations, Books/ filename) ──
# Built from the actual PDFs in hector/api/data/Books/
_KNOWN_ACTS: list[tuple[list[str], str, str, str]] = [
    (["ipc", "indian penal code", "penal code"], "Indian Penal Code, 1860", "IPC", "Indian_Penal_Code_1860.pdf"),
    (["bns", "bharatiya nyaya sanhita", "nyaya sanhita"], "Bharatiya Nyaya Sanhita, 2023", "BNS", "Bharatiya_Nyaya_Sanhita_2023.pdf"),
    (["crpc", "code of criminal procedure", "criminal procedure"], "Code of Criminal Procedure, 1973", "CrPC", "Code_of_Criminal_Procedure_1973.pdf"),
    (["bnss", "bharatiya nagarik suraksha", "suraksha sanhita"], "Bharatiya Nagarik Suraksha Sanhita, 2023", "BNSS", "Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf"),
    (["evidence act", "indian evidence act", "iea"], "Indian Evidence Act, 1872", "IEA", "Indian_Evidence_Act_1872.pdf"),
    (["bsa", "bharatiya sakshya adhiniyam", "sakshya"], "Bharatiya Sakshya Adhiniyam, 2023", "BSA", "Bharatiya_Sakshya_Adhiniyam_2023.pdf"),
    (["cpc", "code of civil procedure", "civil procedure"], "Code of Civil Procedure, 1908", "CPC", "Code_Of_Civil_Procedure_1908.pdf"),
    (["contract act", "indian contract act", "section 23", "section 73"], "Indian Contract Act, 1872", "", "Indian_Contract_Act_1872.pdf"),
    (["tpa", "transfer of property act", "property act"], "Transfer of Property Act, 1882", "TPA", "Transfer_of_Property_Act_1882.pdf"),
    (["ni act", "negotiable instruments", "section 138"], "Negotiable Instruments Act, 1881", "NI Act", "Negotiable_Instruments_Act_1881.pdf"),
    (["constitution", "article 14", "article 19", "article 21", "fundamental rights"], "Constitution of India", "", "Constitution_of_India.pdf"),
    (["motor vehicles act", "mv act", "section 185"], "Motor Vehicles Act, 1988", "", "Motor_Vehicles_Act_1988.pdf"),
    (["hindu marriage act", "section 13"], "Hindu Marriage Act, 1955", "", "Hindu_Marriage_Act_1955.pdf"),
    (["hindu succession act", "section 6"], "Hindu Succession Act, 1956", "", "Hindu_Succession_Act_1956.pdf"),
    (["dowry act", "dowry prohibition", "section 3"], "Dowry Prohibition Act, 1961", "", "Dowry_Prohibition_Act_1961.pdf"),
    (["dv act", "domestic violence act", "protection of women"], "Protection of Women from Domestic Violence Act, 2005", "", "Protection_of_Women_from_Domestic_Violence_Act_2005.pdf"),
    (["ndps act", "narcotic", "section 20"], "Narcotic Drugs and Psychotropic Substances Act, 1985", "NDPS", "Narcotic_Drugs_and_Psychotropic_Substances_Act_1985.pdf"),
    (["consumer protection act", "cpa"], "Consumer Protection Act, 2019", "", "Consumer_Protection_Act_2019.pdf"),
    (["it act", "information technology act", "section 43", "section 66"], "Information Technology Act, 2000", "IT Act", "Information_Technology_Act_2000.pdf"),
    (["limitation act"], "Limitation Act, 1963", "", "Limitation_Act_1963.pdf"),
    (["arbitration act", "section 8", "section 34"], "Arbitration and Conciliation Act, 1996", "", "Arbitration_and_Conciliation_Act_1996.pdf"),
    (["industrial disputes act", "section 25f"], "Industrial Disputes Act, 1947", "IDA", "Industrial_Disputes_Act_1947.pdf"),
    (["family courts act"], "Family Courts Act, 1984", "", "Family_Courts_Act_1984.pdf"),
    (["competition act"], "Competition Act, 2002", "", "Competition_Act_2002.pdf"),
    (["jj act", "juvenile justice act", "section 10"], "Juvenile Justice Act, 2015", "", "Juvenile_Justice_Act_2015.pdf"),
    (["forest act", "section 4"], "Forest Act, 1927", "", "Forest_Act_1927.pdf"),
    (["specific relief act"], "Specific Relief Act, 1963", "", "Specific_Relief_Act_1963.pdf"),
    (["factories act", "section 7a"], "Factories Act, 1948", "", "Factories_Act_1948.pdf"),
    (["easements act"], "Easements Act, 1882", "", "Easements_Act_1882.pdf"),
    (["arms act"], "Arms Act, 1959", "", "Arms_Act_1959.pdf"),
    (["copyright act"], "Copyright Act, 1957", "", "Copyright_Act_1957.pdf"),
    (["environment protection act", "epa"], "Environment Protection Act, 1986", "", "Environment_Protection_Act_1986.pdf"),
    (["rti act", "right to information"], "Right to Information Act, 2005", "RTI", "Right_To_Information_Act_2005.pdf"),
    (["legal services act", "legal services authorities"], "Legal Services Authorities Act, 1987", "", "Legal_Services_Authorities_Act_1987.pdf"),
    (["prevention of corruption act"], "Prevention of Corruption Act, 1988", "", "Prevention_of_Corruption_Act_1988.pdf"),
    (["gram nyayalayas act"], "Gram Nyayalayas Act, 2008", "", "Gram_Nyayalayas_Act_2008.pdf"),
    (["trusts act"], "Trusts Act, 1882", "", "Trusts_Act_1882.pdf"),
    (["hindu minority", "guardianship act"], "Hindu Minority and Guardianship Act, 1956", "", "Hindu_Minority_And_Guardianship_Act_1956.pdf"),
]

# Pre-build a quick-lookup dict for the Books/ directory
_BOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Books")


def _books_exist() -> bool:
    return os.path.isdir(_BOOKS_DIR)


def detect_act_from_query(query: str) -> list[str]:
    """Return list of full act names that the query is likely about."""
    q = query.lower()
    detected = []
    for keywords, full_name, _abbrev, _pdf in _KNOWN_ACTS:
        if any(kw in q for kw in keywords):
            if full_name not in detected:
                detected.append(full_name)
    return detected


def get_act_ingestion_status(query: str) -> str | None:
    """
    Detect which act the query targets, check if it's in Books/,
    and return an honest status message.

    Returns None if the act IS indexed and found in results.
    Returns a user-facing message if the act is missing or not indexed.
    """
    detected = detect_act_from_query(query)
    if not detected:
        return None

    books_dir = _BOOKS_DIR if _books_exist() else None
    messages = []
    for act_name in detected:
        entry = next((e for e in _KNOWN_ACTS if e[1] == act_name), None)
        if not entry:
            continue
        pdf_file = entry[3]
        if books_dir and os.path.isfile(os.path.join(books_dir, pdf_file)):
            # PDF exists in Books/ but wasn't found in results — likely not properly indexed
            messages.append(
                f"The {act_name} is present in our corpus but the specific section "
                f"you're looking for may not be properly indexed yet. "
                f"Our team is working on improving coverage for this act."
            )
        else:
            messages.append(
                f"The {act_name} is not yet included in HECTOR's legal database. "
                f"Our team is actively working on adding it."
            )
    return "\n\n".join(messages) if messages else None


class ResponseFormat:
    """Output format options for generated responses."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    CITATIONS = "citations"


@dataclass
class LegalCitation:
    """Structured citation for legal references."""

    source: str
    page: str | None
    section: str
    act: str
    chapter: str | None = None
    paragraph: str | None = None


class ContextualResponseGenerator:
    """
    Generates contextually rich legal responses with:
    - Hierarchical context (Section → Chapter → Act)
    - Proper citation formatting
    - Multiple output formats
    - Related provisions suggestions
    """

    # Legal-specific system prompt for LLM-enhanced responses
    LEGAL_SYSTEM_PROMPT = """You are HECTOR, a zero-hallucination legal research assistant specializing in Indian law.

RULES:
1. SECTION-NUMBER RULE - this rule outranks every other rule and the OUTPUT FORMAT below.
   Write a section number ONLY when that section's own text appears in the retrieved sources.
   If a related, corresponding, neighbouring or comparative provision exists but its text
   is not in the sources, describe it WITHOUT a number: no "Section N", no "§ N", no
   "Section N(1)", no "cf. Section N", no "up to X years under Section N", no
   comparison-table row or bullet carrying a number absent from the sources.
   When in doubt, leave the number out.
   Hedged guesses are still section numbers and are equally forbidden:
   "likely Section N", "possibly Section N", "probably Section N",
   "Section N or a subsequent provision" - only when that text is present.
    When the retrieved text leaves a cross-reference generic ("the last
    preceding section", "the section above"), keep the generic wording -
    never resolve it to a section number that is absent from the sources.
    MEASURED FAILURES - each was written despite this rule; use the DO rewrite:
      BAD: "the corresponding offence in IPC would be under Section 472."
      DO:  "the corresponding offence in IPC appears in a neighbouring provision
            whose text is not among the sources."
      BAD: "IPC Section 143 assumes the definition from Section 142."
      DO:  "IPC Section 143 takes its definition from a preceding provision whose
            text is not among the sources."
      BAD: "grievous hurt in separate sections (Section 337 and Section 338)"
      DO:  "grievous hurt in a separate provision beside Section 337"
      BAD: "replacing IPC §302" / "e.g., BNS §2(3)" / "death under BNS Section 103"
      DO:  "replacing the earlier IPC murder provision" / "e.g., a general
            definitional provision" / "death under the corresponding BNS provision"
 2. Answer ONLY from the provided source documents. Never invent legal provisions.
 3. Cite every claim with [Source N] where N matches the source number.
 4. Use precise legal terminology (section, clause, proviso, explanation).
 5. If comparing IPC and BNS, compare ONLY sections whose text is in the retrieved sources.
   Never cite a neighbouring or example provision ("e.g. Section N", "cf. Section N",
   "covered elsewhere under Section N") unless that section's own text is in the
   sources - omit the number entirely instead.
6. If the sources don't contain enough information, say so explicitly.
7. Keep answers concise and direct — no filler phrases.

OUTPUT FORMAT:
- Start with a direct answer to the query.
- Then provide the statutory text or key provisions.
- Then note differences between IPC and BNS only for sections present in the sources.
- End with a brief note on practical implications if applicable."""

    # Used when no BNS source was retrieved. Without this branch the model
    # appends "a direct comparison between IPC Section N and its BNS
    # counterpart cannot be made from the available material", which the
    # abstention-clause detector in core.verifier classifies as negated and
    # therefore scores as an ungrounded citation even though the section is
    # present in the retrieved sources.
    LEGAL_SYSTEM_PROMPT_NO_BNS = """You are HECTOR, a zero-hallucination legal research assistant specializing in Indian law.

RULES:
1. SECTION-NUMBER RULE - this rule outranks every other rule and the OUTPUT FORMAT below.
   Write a section number ONLY when that section's own text appears in the retrieved sources.
   If a related, corresponding, neighbouring or comparative provision exists but its text
   is not in the sources, describe it WITHOUT a number: no "Section N", no "§ N", no
   "Section N(1)", no "cf. Section N", no "up to X years under Section N", no
   comparison-table row or bullet carrying a number absent from the sources.
   When in doubt, leave the number out.
   Hedged guesses are still section numbers and are equally forbidden:
   "likely Section N", "possibly Section N", "probably Section N",
   "Section N or a subsequent provision" - only when that text is present.
    When the retrieved text leaves a cross-reference generic ("the last
    preceding section", "the section above"), keep the generic wording -
    never resolve it to a section number that is absent from the sources.
    MEASURED FAILURES - each was written despite this rule; use the DO rewrite:
      BAD: "the corresponding offence would be under Section 472."
      DO:  "the corresponding offence appears in a neighbouring provision whose
            text is not among the sources."
      BAD: "IPC Section 143 assumes the definition from Section 142."
      DO:  "IPC Section 143 takes its definition from a preceding provision whose
            text is not among the sources."
      BAD: "...and Section 338" / "replacing IPC §302" / "e.g., §2(3)"
      DO:  "...and the grievous-hurt provision beside it" / "replacing the earlier
            murder provision" / "e.g., a general definitional provision"
 2. Answer ONLY from the provided source documents. Never invent legal provisions.
3. Cite every claim with [Source N] where N matches the source number.
4. Use precise legal terminology (section, clause, proviso, explanation).
5. If the sources don't contain enough information, say so explicitly.
6. Keep answers concise and direct — no filler phrases.
7. Do not mention, compare against, or speculate about other codes (BNS, BNSS, BSA) unless a source for them is among the retrieved sources.

OUTPUT FORMAT:
- Start with a direct answer to the query.
- Then provide the statutory text or key provisions.
- End with a brief note on practical implications if applicable."""

    @staticmethod
    def _has_bns_source(results: list[dict]) -> bool:
        """True when at least one retrieved chunk belongs to a new code."""
        for r in results or []:
            meta = r.get("metadata") or {}
            blob = " ".join(
                str(meta.get(k) or "")
                for k in ("real_act_name", "act_name", "abbreviation", "source")
            ).lower()
            if "nyaya sanhita" in blob or "bns" in blob:
                return True
        return False

    ABSTENTION_MESSAGE = (
        "I could not find sufficiently relevant sources in the indexed legal "
        "corpus to answer this question, so I am not generating an answer. "
        "Please rephrase using a specific section, act, or legal issue."
    )

    def __init__(self, retriever: "HectorHybridRetriever"):
        self.retriever = retriever
        self._nim_client = None
        self._nim_last_failure = 0  # timestamp of last NIM failure
        self._nim_cooldown = 60  # seconds to wait before retrying NIM

    def _get_nim_client(self):
        import time as _time
        now = _time.time()
        # Reset NIM client after cooldown period
        if self._nim_client is False and (now - self._nim_last_failure) > self._nim_cooldown:
            self._nim_client = None
        if self._nim_client is None:
            try:
                from core.nim_llm import get_nim_llm, NIM_MODELS

                self._nim_client = get_nim_llm()
                self._generation_model = NIM_MODELS["generation"]
            except Exception:
                self._nim_client = False
                self._nim_last_failure = now
        return self._nim_client if self._nim_client is not False else None

    def _synthesize_with_llm(
        self, query: str, results: list[dict], file_context: str | None = None
    ) -> str | None:
        """Call NVIDIA NIM to synthesize a legal answer from retrieved chunks."""
        nim = self._get_nim_client()
        if nim is None:
            return None

        context_parts = []

        # File context is Source 0 — always listed first with highest priority
        if file_context:
            context_parts.append(
                f"[Source 0: Uploaded Document]\n{file_context[:10000]}"
            )

        for i, r in enumerate(results[:5], 1):
            doc = r.get("document", "")
            meta = r.get("metadata", {})
            citation = r.get("citation", {})
            act = (
                meta.get("real_act_name")
                or meta.get("act_name")
                or meta.get("act")
                or "Unknown"
            )
            section = citation.get("section") or meta.get("section_number") or ""
            page = meta.get("page") or ""
            label = f"[Source {i}: {act}"
            if section:
                label += f", Section {section}"
            if page:
                label += f", Page {page}"
            label += "]"
            if len(doc) <= 5000:
                body = doc
            else:
                body = (
                    doc[:3000]
                    + "\n[... middle of this section omitted to fit the prompt ...]\n"
                    + doc[-2000:]
                )
            context_parts.append(f"{label}\n{body}")

        context = "\n\n---\n\n".join(context_parts)

        priority_hint = ""
        if file_context:
            priority_hint = (
                "\n\nIMPORTANT: The user uploaded a document (Source 0). "
                "When the query relates to content in Source 0, prioritize and answer "
                "from the uploaded document FIRST. Only use other sources to supplement "
                "or cross-reference.\n"
            )

        has_bns = self._has_bns_source(results)
        system_prompt = (
            self.LEGAL_SYSTEM_PROMPT if has_bns else self.LEGAL_SYSTEM_PROMPT_NO_BNS
        )
        compare_hint = (
            "Compare IPC and BNS if both are present."
            if has_bns
            else "Answer only from the retrieved sources; do not introduce other codes."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Query: {query}\n\nRetrieved Sources:\n{context}\n\n"
                "Provide a direct, well-structured answer. "
                f"Cite with [Source N]. {compare_hint}"
                f"{priority_hint}",
            },
        ]

        try:
            return nim.chat(
                messages,
                temperature=0.0,
                # 1024 cut ~30/102 cmp1 answers mid-sentence/mid-number
                # ("(BNS Section 1", "IPC Section 477") - fake ungrounded
                # mentions; full compare answers need more room.
                max_tokens=2048,
                model=getattr(self, "_generation_model", None),
            )
        except Exception as e:
            logger.warning("NIM synthesis failed: %s", e)
            return None

    def generate(
        self,
        query: str,
        results: list[dict],
        format: str = ResponseFormat.SUMMARY,
        include_related: bool = True,
        file_context: str | None = None,
    ) -> dict:
        """
        Generate a formatted response from retrieval results.

        Returns:
            Dictionary with generated_response, answer_sections, source_sections,
            etc. When no sources clear the relevance threshold, generation is
            skipped and an explicit abstention is returned with "abstained": True
            and zero citations.
        """
        if not results and not file_context:
            logger.info("abstained (no sources): query=%r", query[:80])
            return {
                "generated_response": self.ABSTENTION_MESSAGE,
                "answer_sections": [
                    {
                        "title": "No grounded sources",
                        "body": self.ABSTENTION_MESSAGE,
                        "rows": [],
                    }
                ],
                "source_sections": [],
                "answer_confidence": 0.0,
                "citations": [],
                "related_provisions": [],
                "abstained": True,
            }

        citations = self._extract_citations(results)
        related = self._find_related_provisions(results) if include_related else []
        structured = self._build_legal_rag_payload(results, query=query)

        # Try LLM synthesis — if it works, use it as the primary answer body
        llm_response = (
            self._synthesize_with_llm(query, results, file_context=file_context)
            if results
            else None
        )
        if llm_response:
            # Replace the Grounded Answer body with the LLM response
            if structured["answer_sections"]:
                structured["answer_sections"][0]["body"] = llm_response
            response = llm_response
        else:
            response = self._format_legal_rag(query, results, related)

        # Inject file context as a source if provided
        source_sections = structured["source_sections"]
        if file_context:
            source_sections = [
                {
                    "act": "Uploaded Document",
                    "section": "User-provided file",
                    "similarity": 1.0,
                    "snippet": file_context[:500],
                }
            ] + source_sections

        return {
            "generated_response": response,
            "answer_sections": structured["answer_sections"],
            "source_sections": source_sections,
            "answer_confidence": structured["answer_confidence"],
            "citations": [self._citation_to_dict(c) for c in citations],
            "related_provisions": related,
            "abstained": is_abstention_answer(response),
        }

    def _build_legal_rag_payload(self, results: list[dict], query: str = "") -> dict:
        if not results:
            return {
                "answer_sections": [
                    {
                        "title": "Result",
                        "body": "No relevant sources found for this query.",
                        "rows": [],
                    }
                ],
                "source_sections": [],
                "answer_confidence": 0.0,
            }

        _act_status_hint = get_act_ingestion_status(query) if query else None

        all_sources = [
            self._source_payload(item, index, len(results))
            for index, item in enumerate(results, start=1)
        ]
        sources = [
            s for s in all_sources if s["similarity"] >= 0.70
        ]
        # Fallback to all sources if high-similarity filter removed everything
        effective_sources = sources if sources else all_sources
        ipc_sources = [
            source
            for source in effective_sources
            if any(
                kw in source["act"]
                for kw in ("IPC", "INDIAN PENAL CODE")
            )
        ]
        bns_sources = [
            source
            for source in effective_sources
            if any(
                kw in source["act"]
                for kw in ("BNS", "BHARATIYA NYAYA SANHITA")
            )
        ]

        overview_lines = []
        if ipc_sources:
            source = self._best_source(ipc_sources, query=query)
            overview_lines.append(
                f"Indian Penal Code, 1860 [IPC]: {self._framework_sentence(source)} [S{source['number']}]"
            )
        elif _act_status_hint:
            overview_lines.append(
                f"Indian Penal Code, 1860 [IPC]: {_act_status_hint}"
            )
        elif sources:
            source = self._best_source(sources, query=query)
            act_name = source.get("act", "related source")
            overview_lines.append(
                f"Indian Penal Code, 1860 [IPC]: No direct IPC bare act section retrieved. "
                f"Nearest related provision found in {act_name}, Section {source['section']}. [S{source['number']}]"
            )
        else:
            overview_lines.append(
                "Indian Penal Code, 1860 [IPC]: No relevant sources found for this query."
            )

        if bns_sources:
            source = self._best_source(bns_sources, query=query)
            overview_lines.append(
                f"Bharatiya Nyaya Sanhita, 2023 [BNS]: {self._framework_sentence(source)} [S{source['number']}]"
            )
        elif _act_status_hint:
            overview_lines.append(
                f"Bharatiya Nyaya Sanhita, 2023 [BNS]: {_act_status_hint}"
            )
        elif sources:
            source = self._best_source(sources, query=query)
            act_name = source.get("act", "related source")
            overview_lines.append(
                f"Bharatiya Nyaya Sanhita, 2023 [BNS]: No direct BNS bare act section retrieved. "
                f"Nearest related provision found in {act_name}, Section {source['section']}. [S{source['number']}]"
            )
        else:
            overview_lines.append(
                "Bharatiya Nyaya Sanhita, 2023 [BNS]: No relevant sources found for this query."
            )

        if (ipc_sources or sources) and (bns_sources or sources):
            ipc = self._best_source(ipc_sources, query=query) if ipc_sources else self._best_source(sources, query=query)
            bns = self._best_source(bns_sources, query=query) if bns_sources else self._best_source(sources, query=query)
            if ipc_sources and bns_sources:
                overview_lines.append(
                    f"Key difference: the retrieved IPC source is centred on Section {ipc['section']} IPC, while the retrieved BNS source is centred on Section {bns['section']} BNS. [S{ipc['number']}] [S{bns['number']}]"
                )

        all_rows = [
            {
                "point": "Section reference",
                "ipc": self._table_section(ipc_sources, "IPC", query=query),
                "bns": self._table_section(bns_sources, "BNS", query=query),
            },
            {
                "point": "Simple/basic offence punishment",
                "ipc": self._table_punishment(ipc_sources, query=query),
                "bns": self._table_punishment(bns_sources, query=query),
            },
            {
                "point": "Repeat/aggravated offence punishment",
                "ipc": self._table_aggravated(ipc_sources, query=query),
                "bns": self._table_aggravated(bns_sources, query=query),
            },
            {
                "point": "Cognisable status",
                "ipc": self._table_status(ipc_sources, query=query),
                "bns": self._table_status(bns_sources, query=query),
            },
        ]
        # Only keep rows where at least one side has real data
        comparison_rows = [
            row for row in all_rows
            if row["ipc"] != "Not directly stated" or row["bns"] != "Not directly stated"
        ]

        answer_sections = [
            {
                "title": "Grounded Answer",
                "body": "\n".join(overview_lines),
                "rows": [],
            },
        ]
        if comparison_rows:
            answer_sections.append({
                "title": "Comparison",
                "body": "",
                "rows": comparison_rows,
            })

        return {
            "answer_sections": answer_sections,
            "source_sections": sources,
            "answer_confidence": float(self._answer_confidence(sources)),
        }

    def _format_legal_rag(
        self, query: str, results: list[dict], related: list[str]
    ) -> str:
        """Format a response using the HECTOR Research Report format."""
        if not results:
            act_status = get_act_ingestion_status(query)
            if act_status:
                return (
                    f"[HECTOR Intelligence Report] · [0 sources retrieved] · Query: {query}\n\n"
                    f"{act_status}\n\n"
                    "Note: This information is provided for research purposes and does not constitute formal legal advice."
                )
            return (
                f"[HECTOR Intelligence Report] · [0 sources retrieved] · Query: {query}\n\n"
                "No relevant sources found for this query.\n\n"
                "Note: This information is provided for research purposes and does not constitute formal legal advice."
            )

        sources = [
            self._source_payload(item, index, len(results))
            for index, item in enumerate(results, start=1)
        ]
        ipc_sources = [
            source
            for source in sources
            if any(
                kw in source["act"]
                for kw in ("IPC", "INDIAN PENAL CODE")
            )
        ]
        bns_sources = [
            source
            for source in sources
            if any(
                kw in source["act"]
                for kw in ("BNS", "BHARATIYA NYAYA SANHITA")
            )
        ]

        act_status_hint = get_act_ingestion_status(query)

        lines = [
            f"[HECTOR Intelligence Report] · [{len(sources)} sources retrieved] · Query: {query}",
            "",
        ]

        if ipc_sources:
            source = self._best_source(ipc_sources, query=query)
            lines.append(
                f"**Indian Penal Code, 1860** [IPC]: {self._framework_sentence(source)} [§{source['number']}]"
            )
        elif act_status_hint:
            lines.append(
                f"**Indian Penal Code, 1860** [IPC]: {act_status_hint}"
            )
        elif sources:
            source = self._best_source(sources, query=query)
            act_name = source.get("act", "related source")
            lines.append(
                f"**Indian Penal Code, 1860** [IPC]: No direct IPC bare act section retrieved. "
                f"Nearest related provision found in {act_name}, Section {source['section']}. [§{source['number']}]"
            )
        else:
            lines.append(
                "**Indian Penal Code, 1860** [IPC]: No relevant sources found for this query."
            )

        if bns_sources:
            source = self._best_source(bns_sources, query=query)
            lines.append(
                f"**Bharatiya Nyaya Sanhita, 2023** [BNS]: {self._framework_sentence(source)} [§{source['number']}]"
            )
        elif act_status_hint:
            lines.append(
                f"**Bharatiya Nyaya Sanhita, 2023** [BNS]: {act_status_hint}"
            )
        elif sources:
            source = self._best_source(sources, query=query)
            act_name = source.get("act", "related source")
            lines.append(
                f"**Bharatiya Nyaya Sanhita, 2023** [BNS]: No direct BNS bare act section retrieved. "
                f"Nearest related provision found in {act_name}, Section {source['section']}. [§{source['number']}]"
            )
        else:
            lines.append(
                "**Bharatiya Nyaya Sanhita, 2023** [BNS]: No relevant sources found for this query."
            )

        if (ipc_sources or sources) and (bns_sources or sources):
            ipc = self._best_source(ipc_sources, query=query) if ipc_sources else self._best_source(sources, query=query)
            bns = self._best_source(bns_sources, query=query) if bns_sources else self._best_source(sources, query=query)
            if ipc_sources and bns_sources:
                lines.append(
                    f"Key difference: the retrieved IPC source is centred on Section {ipc['section']} IPC, while the retrieved BNS source is centred on Section {bns['section']} BNS. [S{ipc['number']}] [S{bns['number']}]"
                )

        lines.extend(
            [
                "",
                "| Comparison point | Indian Penal Code, 1860 [IPC] | Bharatiya Nyaya Sanhita, 2023 [BNS] |",
            ]
        )
        lines.append("| --- | --- | --- |")
        lines.append(
            f"| Section reference (definition) | {self._table_section(ipc_sources, 'IPC', query=query)} | {self._table_section(bns_sources, 'BNS', query=query)} |"
        )
        lines.append(
            f"| Simple/basic offence punishment | {self._table_punishment(ipc_sources, query=query)} | {self._table_punishment(bns_sources, query=query)} |"
        )
        lines.append(
            f"| Repeat/aggravated offence punishment | {self._table_aggravated(ipc_sources, query=query)} | {self._table_aggravated(bns_sources, query=query)} |"
        )
        lines.append(
            f"| Cognisable status | {self._table_status(ipc_sources, query=query)} | {self._table_status(bns_sources, query=query)} |"
        )

        lines.extend(["", "STATUTORY SOURCES", ""])
        for source in sources:
            lines.append(
                f"[§{source['number']}]  {source['title']} Section {source['section']} {source['act']}"
            )
            lines.append(f"        Document type: {source['document_type']}")
            lines.append(
                f"        Chunk: {source['chunk']} of {source['total_chunks']}"
            )
            lines.append(f"        Similarity: {source['similarity']:.2f} score")
            lines.append(f'        Excerpt: "{source["excerpt"]}"')
            lines.append("")

        confidence = self._answer_confidence(sources)
        confidence_line = f"Answer confidence: {confidence}%"
        if sources and sources[0]["similarity"] < 0.70:
            confidence_line += (
                " Low confidence — retrieved sources may not fully cover this query."
            )
        lines.append(confidence_line)
        lines.append("")
        lines.append(
            "Note: This information is provided for research purposes and does not constitute formal legal advice."
        )
        return "\n".join(lines)

    def _source_payload(self, item: dict, number: int, total_chunks: int) -> dict:
        metadata = item.get("metadata", {}) or {}
        citation = item.get("citation", {}) or {}
        document = " ".join((item.get("document") or "").split())
        act = (
            item.get("act")
            or metadata.get("real_act_name")
            or metadata.get("act_name")
            or metadata.get("act")
            or ""
        ).upper() or "LEGAL"
        section = (
            citation.get("section") or metadata.get("section_number") or "unidentified"
        )
        # Use real_act_name as primary title (accurate document name)
        title = (
            metadata.get("real_act_name")
            or metadata.get("act_name")
            or metadata.get("source")
            or "Retrieved legal source"
        )
        score = self._normalize_score(
            float(item.get("similarity_score", item.get("score", 0.0)) or 0.0)
        )

        return {
            "number": number,
            "title": title,
            "source_id": item.get("id"),
            "act": act,
            "section": section,
            "document_type": self._document_type(metadata),
            "chunk": int(metadata.get("chunk_index", number - 1) or 0) + 1,
            "total_chunks": total_chunks,
            "similarity": score,
            "excerpt": self._best_excerpt(document),
            "document": document,
            "reasons": item.get("reasons") or [],
        }

    _QUERY_STOPWORDS = frozenset({
        "the", "and", "for", "with", "under", "from", "this", "that", "what",
        "which", "does", "are", "was", "were", "been", "being", "have", "has",
        "had", "shall", "must", "may", "can", "not", "any", "all", "its",
        "their", "there", "then", "than", "when", "who", "whom", "how", "why",
        "into", "upon", "said", "says", "also", "but", "you", "your", "our",
        "them", "they", "please", "tell", "give", "explain", "about",
        "between", "among", "within", "please", "kindly", "regarding",
    })

    def _query_tokens(self, query: str) -> set[str]:
        tokens = set(re.findall(r"[a-z0-9]{3,}", (query or "").lower()))
        return tokens - self._QUERY_STOPWORDS

    def _doc_tokens(self, document: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]{3,}", (document or "").lower()))

    def _best_source(self, sources: list[dict], query: str = "") -> dict:
        if query and sources:
            q_tokens = self._query_tokens(query)
            if q_tokens:
                matching = [
                    source for source in sources
                    if q_tokens & self._doc_tokens(source["document"])
                ]
                if matching:
                    sources = matching
        return max(sources, key=lambda source: source["similarity"])

    def _normalize_score(self, score: float) -> float:
        if score <= 0:
            return 0.0
        if score <= 1:
            return score
        return 1.0

    def _document_type(self, metadata: dict) -> str:
        structure_type = str(metadata.get("structure_type", "")).lower()
        source = str(metadata.get("source", "")).lower()
        if "case" in structure_type or "judgment" in source:
            return "Case law"
        if "regulation" in structure_type:
            return "Regulation"
        if (
            "commentary" in structure_type
            or "textbook" in source
            or "ratanlal" in source
        ):
            return "Legal commentary"
        return "Statute"

    def _best_excerpt(self, document: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", document)
        keywords = (
            "punish",
            "imprison",
            "fine",
            "theft",
            "section",
            "cognizable",
            "cognisable",
            "community service",
        )
        for sentence in sentences:
            if "punishment for theft" in sentence.lower():
                excerpt = sentence.strip()
                words = excerpt.split()
                if len(words) > 40:
                    excerpt = " ".join(words[:40]).rstrip(",;:") + "..."
                return excerpt.replace('"', "'")

        ranked = sorted(
            (sentence.strip() for sentence in sentences if sentence.strip()),
            key=lambda sentence: sum(
                keyword in sentence.lower() for keyword in keywords
            ),
            reverse=True,
        )
        excerpt = ranked[0] if ranked else document[:220]
        words = excerpt.split()
        if len(words) > 40:
            excerpt = " ".join(words[:40]).rstrip(",;:") + "..."
        return excerpt.replace('"', "'")

    def _framework_sentence(self, source: dict) -> str:
        excerpt = source["excerpt"].rstrip(".")
        return f'Section {source["section"]} {source["act"]} is the retrieved provision; the source states: "{excerpt}."'

    def _table_section(self, sources: list[dict], act: str, query: str = "") -> str:
        if not sources:
            return "No direct source retrieved"
        source = self._best_source(sources, query=query)
        return f"Section {source['section']} {act} [§{source['number']}]"

    def _table_punishment(self, sources: list[dict], query: str = "") -> str:
        source = self._first_matching_source(
            sources, ("punish", "imprison", "fine", "community service"),
            query=query,
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _table_aggravated(self, sources: list[dict], query: str = "") -> str:
        source = self._first_matching_source(
            sources, ("subsequent", "repeat", "aggravated", "second", "again"),
            query=query,
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _table_status(self, sources: list[dict], query: str = "") -> str:
        source = self._first_matching_source(
            sources, ("cognizable", "cognisable", "bailable", "non-cognizable"),
            query=query,
        )
        if not source:
            return "Not directly stated"
        return f"{source['excerpt']} [§{source['number']}]"

    def _first_matching_source(
        self, sources: list[dict], keywords: tuple[str, ...], query: str = ""
    ) -> dict | None:
        if query and sources:
            q_tokens = self._query_tokens(query)
            if q_tokens:
                matching = [
                    source for source in sources
                    if q_tokens & self._doc_tokens(source["document"])
                ]
                if matching:
                    matched_ids = {id(source) for source in matching}
                    sources = matching + [
                        source for source in sources
                        if id(source) not in matched_ids
                    ]
        for source in sources:
            haystack = source["document"].lower()
            if any(keyword in haystack for keyword in keywords):
                return source
        return sources[0] if sources else None

    def _answer_confidence(self, sources: list[dict]) -> int:
        weighted_total = 0.0
        weight_sum = 0.0
        for index, source in enumerate(sources[:5], start=1):
            weight = 1.0 / index
            weighted_total += source["similarity"] * weight
            weight_sum += weight
        return round((weighted_total / max(weight_sum, 1e-9)) * 100)

    def _extract_citations(self, results: list[dict]) -> list[LegalCitation]:
        """Extract structured citations from retrieval results."""
        citations = []

        for item in results:
            metadata = item.get("metadata", {}) or {}
            citation = LegalCitation(
                source=metadata.get("source", "Unknown"),
                page=metadata.get("page"),
                section=metadata.get("section_number", ""),
                act=metadata.get("act_name", metadata.get("act", "")),
                chapter=metadata.get("chapter"),
            )
            citations.append(citation)

        return citations

    def _format_summary(
        self,
        query: str,
        results: list[dict],
        citations: list[LegalCitation],
        related: list[str],
    ) -> str:
        """Format results as a concise summary."""
        lines = []

        # Add relevant content from top results
        for item in results[:3]:
            doc = item.get("document", "")
            if doc:
                # Take first 300 chars of relevant content
                snippet = doc[:300].strip()
                if len(doc) > 300:
                    snippet += "..."
                lines.append(snippet)
                lines.append("")

        # Add citations
        if citations:
            lines.append("---")
            lines.append("**Citations:**")
            for cit in citations[:5]:
                cit_str = f"• {cit.act}"
                if cit.section:
                    cit_str += f" Section {cit.section}"
                if cit.page:
                    cit_str += f", Page {cit.page}"
                if cit.source and cit.source != "Unknown":
                    cit_str += f" ({cit.source})"
                lines.append(cit_str)

        # Add related provisions
        if related:
            lines.append("")
            lines.append("**Related Provisions:**")
            for rel in related[:5]:
                lines.append(f"• {rel}")

        return "\n".join(lines)

    def _format_detailed(
        self,
        query: str,
        results: list[dict],
        citations: list[LegalCitation],
        related: list[str],
    ) -> str:
        """Format results as detailed analysis with full context."""
        lines = []

        # Query context
        lines.append(f"**Query:** {query}")
        lines.append("")

        # Hierarchical context from top result
        if results:
            metadata = results[0].get("metadata", {}) or {}
            act = metadata.get("act_name") or metadata.get("act", "")
            chapter = metadata.get("chapter", "")
            section = metadata.get("section_number", "")
            section_title = metadata.get("section_title", "")

            if act:
                lines.append(f"**Act:** {act}")
            if chapter:
                lines.append(f"**Chapter:** {chapter}")
            if section:
                lines.append(
                    f"**Section:** {section}"
                    + (f" - {section_title}" if section_title else "")
                )
            lines.append("")

        # Full content from results
        lines.append("---")
        lines.append("**Relevant Legal Text:**")
        lines.append("")
        for i, item in enumerate(results[:5], 1):
            doc = item.get("document", "")
            if doc:
                lines.append(f"### Source {i}")
                lines.append(doc)
                lines.append("")

        # Detailed citations
        lines.append("---")
        lines.append("**Citations:**")
        for cit in citations:
            parts = [cit.act]
            if cit.chapter:
                parts.append(f"Chapter: {cit.chapter}")
            if cit.section:
                parts.append(f"Section {cit.section}")
            if cit.page:
                parts.append(f"Page {cit.page}")
            if cit.source and cit.source != "Unknown":
                parts.append(f"Source: {cit.source}")
            lines.append("• " + ", ".join(parts))

        # Related provisions
        if related:
            lines.append("")
            lines.append("**Related Provisions:**")
            for rel in related:
                lines.append(f"• {rel}")

        return "\n".join(lines)

    def _format_citations_only(self, citations: list[LegalCitation]) -> str:
        """Format as a pure citation list."""
        if not citations:
            return "No citations available."

        lines = ["**Citations:**", ""]
        for i, cit in enumerate(citations, 1):
            parts = [f"{i}. {cit.act}"]
            if cit.section:
                parts.append(f"Section {cit.section}")
            if cit.chapter:
                parts.append(f"Chapter: {cit.chapter}")
            if cit.page:
                parts.append(f"Page {cit.page}")
            if cit.source and cit.source != "Unknown":
                parts.append(f"({cit.source})")
            lines.append(" ".join(parts))

        return "\n".join(lines)

    def _find_related_provisions(self, results: list[dict]) -> list[str]:
        """Find related provisions based on metadata."""
        related = set()
        primary_act = None
        primary_chapter = None

        # Get primary context
        if results:
            metadata = results[0].get("metadata", {}) or {}
            primary_act = metadata.get("act_name") or metadata.get("act")
            primary_chapter = metadata.get("chapter")

        # Find related from other results
        for item in results[1:]:
            metadata = item.get("metadata", {}) or {}
            act = metadata.get("act_name") or metadata.get("act")
            section = metadata.get("section_number", "")
            chapter = metadata.get("chapter")

            # Same act, different chapter/section
            if act == primary_act and section:
                related.add(f"{act} Section {section}")

            # Same chapter, different section
            if chapter == primary_chapter and chapter and section:
                related.add(f"Section {section}")

        return list(related)[:10]

    def _citation_to_dict(self, citation: LegalCitation) -> dict:
        """Convert LegalCitation to dictionary."""
        return {
            "source": citation.source,
            "page": citation.page,
            "section": citation.section,
            "act": citation.act,
            "chapter": citation.chapter,
        }


def format_citation(source: str, page: str | None, section: str, act: str) -> str:
    """Format a single citation string."""
    parts = [f"Section {section} {act}"]
    if page:
        parts.append(f"Page {page}")
    if source and source != "Unknown":
        parts.append(f"({source})")
    return ", ".join(parts)
