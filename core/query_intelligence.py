"""
Query Intelligence (QI) Layer for HECTOR.

Sits between raw user query and the retrieval pipeline.
Uses NVIDIA Nemotron Nano 8B to analyze the query and output
structured JSON that the retriever can act on.

Handles:
- Cross-act mapping (IPC 302 → BNS 101)
- Entity extraction (acts, sections, concepts)
- Query rewriting for better retrieval
- Metadata filter generation
- Search strategy selection
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("hector.query_intelligence")

# Load the IPC→BNS mapping once at module level
_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "mapping.json")
try:
    with open(_MAPPING_PATH, "r", encoding="utf-8") as f:
        _MAPPING_DATA = json.load(f)
    IPC_TO_BNS: dict[str, dict] = _MAPPING_DATA.get("IPC_TO_BNS", {})
except (FileNotFoundError, json.JSONDecodeError):
    IPC_TO_BNS = {}

# Build reverse map: BNS section → IPC section
BNS_TO_IPC: dict[str, str] = {}
for ipc_sec, data in IPC_TO_BNS.items():
    bns_sec = data.get("new", "")
    if bns_sec:
        BNS_TO_IPC[bns_sec] = ipc_sec

# Known act names for the system prompt
KNOWN_ACTS = [
    "Indian Penal Code, 1860 (IPC)",
    "Bharatiya Nyaya Sanhita, 2023 (BNS)",
    "Code of Criminal Procedure, 1973 (CrPC)",
    "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
    "Indian Evidence Act, 1872 (IEA)",
    "Bharatiya Sakshya Adhiniyam, 2023 (BSA)",
    "Code of Civil Procedure, 1908 (CPC)",
    "Indian Contract Act, 1872",
    "Transfer of Property Act, 1882",
    "Hindu Marriage Act, 1955",
    "Hindu Succession Act, 1956",
    "Dowry Prohibition Act, 1961",
    "Negotiable Instruments Act, 1881",
    "Motor Vehicles Act, 1988",
    "Consumer Protection Act, 2019",
    "Information Technology Act, 2000",
    "Arbitration and Conciliation Act, 1996",
    "Limitation Act, 1963",
    "Specific Relief Act, 1963",
    "Industrial Disputes Act, 1947",
    "Arms Act, 1959",
    "Narcotic Drugs and Psychotropic Substances Act, 1985",
    "Legal Services Authorities Act, 1987",
    "Copyright Act, 1957",
    "Competition Act, 2002",
    "Protection of Women from Domestic Violence Act, 2005",
    "Family Courts Act, 1984",
    "Juvenile Justice Act, 2015",
    "Right to Information Act, 2005",
    "Forest Act, 1927",
    "Environment Protection Act, 1986",
    "Factories Act, 1948",
    "Easements Act, 1882",
    "Indian Trusts Act, 1882",
]

QI_SYSTEM_PROMPT = """You are HECTOR Query Intelligence, a legal query analyzer for Indian law.

Your job: Analyze the user's query and return a JSON object that tells the retrieval system exactly what to search for.

You have access to the IPC→BNS cross-reference mapping. Use it when the query references IPC sections.

IPC→BNS KEY MAPPINGS (most important ones):
- IPC 302 → BNS 101 (Murder)
- IPC 304 → BNS 103 (Culpable homicide)
- IPC 304B → BNS 80 (Dowry death)
- IPC 376 → BNS 63 (Rape)
- IPC 379 → BNS 304 (Theft)
- IPC 303 → BNS 102 (Murder by life-convict)
- IPC 147-148 → BNS 191-192 (Rioting)
- IPC 149 → BNS 190 (Unlawful assembly)
- IPC 120A-120B → BNS 61-62 (Criminal conspiracy)
- IPC 34 → BNS 3 (Common intention)
- IPC 141-149 → BNS 189-190 (Unlawful assembly)
- IPC 323 → BNS 115 (Voluntarily causing hurt)
- IPC 498A → BNS 85-86 (Cruelty by husband/relatives)
- IPC 506 → BNS 351 (Criminal intimidation)
- IPC 420 → BNS 318 (Cheating)
- IPC 406 → BNS 316 (Criminal breach of trust)
- IPC 354 → BNS 74 (Assault on woman with intent to outrage modesty)
- IPC 299 → BNS 100 (Culpable homicide)
- IPC 300 → BNS 101 (Murder definition)
- IPC 301 → BNS 104 (Causing death by negligence)
- IPC 307 → BNS 109 (Attempt to murder)
- IPC 308 → BNS 110 (Attempt to commit culpable homicide)
- IPC 375-376 → BNS 63-64 (Rape)
- IPC 392-395 → BNS 309-312 (Robbery/dacoity)
- IPC 425-426 → BNS 329-330 (Mischief)
- IPC 441-447 → BNS 324-325 (Criminal trespass)
- IPC 463-471 → BNS 336-340 (Forgery)
- IPC 493-498 → BNS 82-86 (Matrimonial offences)
- IPC 509 → BNS 79 (Outraging modesty)

RULES:
1. ALWAYS return valid JSON. No text before or after.
2. If the query mentions "IPC Section X" or "Section X IPC", look up the BNS equivalent.
3. If the query mentions "BNS Section X", look up the IPC equivalent if it exists.
4. If the query asks for "equivalent", "counterpart", "replaced by", "corresponding" — this is a cross-act mapping query.
5. For cross-act mapping queries, search for BOTH the source and target sections.
6. Expand vague queries into specific section searches.

OUTPUT FORMAT (strict JSON):
{
    "intent": "cross_act_mapping" | "section_lookup" | "comparison" | "concept_search" | "general_legal",
    "confidence": 0.0-1.0,
    "source_act": "IPC" | "BNS" | "CrPC" | "BNSS" | "BSA" | "CPC" | null,
    "source_section": "302" | null,
    "target_act": "BNS" | "IPC" | null,
    "target_section": "101" | null,
    "legal_concepts": ["murder", "punishment"],
    "rewritten_queries": ["Section 101 BNS murder punishment", "Section 302 IPC murder punishment"],
    "metadata_filters": {
        "act_name": ["Indian Penal Code, 1860", "Bharatiya Nyaya Sanhita, 2023"],
        "section_number": ["302", "101"]
    },
    "search_strategy": "filtered_dual_act" | "filtered_single_act" | "unfiltered_broad" | "concept_expansion"
}"""


@dataclass
class QueryAnalysis:
    """Structured output from the Query Intelligence layer."""

    intent: str = "general_legal"
    confidence: float = 0.5
    source_act: str | None = None
    source_section: str | None = None
    target_act: str | None = None
    target_section: str | None = None
    legal_concepts: list[str] = field(default_factory=list)
    rewritten_queries: list[str] = field(default_factory=list)
    metadata_filters: dict[str, list[str]] = field(default_factory=dict)
    search_strategy: str = "unfiltered_broad"
    mapping_info: str | None = None
    raw_json: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "source_act": self.source_act,
            "source_section": self.source_section,
            "target_act": self.target_act,
            "target_section": self.target_section,
            "legal_concepts": self.legal_concepts,
            "rewritten_queries": self.rewritten_queries,
            "metadata_filters": self.metadata_filters,
            "search_strategy": self.search_strategy,
            "mapping_info": self.mapping_info,
        }


# ── Act name normalization ──────────────────────────────────────────────

ACT_ALIASES = {
    "ipc": "Indian Penal Code, 1860",
    "indian penal code": "Indian Penal Code, 1860",
    "bns": "Bharatiya Nyaya Sanhita, 2023",
    "bharatiya nyaya sanhita": "Bharatiya Nyaya Sanhita, 2023",
    "crpc": "Code of Criminal Procedure, 1973",
    "code of criminal procedure": "Code of Criminal Procedure, 1973",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "bharatiya nagarik suraksha sanhita": "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "bsa": "Bharatiya Sakshya Adhiniyam, 2023",
    "bharatiya sakshya adhiniyam": "Bharatiya Sakshya Adhiniyam, 2023",
    "iea": "Indian Evidence Act, 1872",
    "indian evidence act": "Indian Evidence Act, 1872",
    "evidence act": "Indian Evidence Act, 1872",
    "cpc": "Code of Civil Procedure, 1908",
    "code of civil procedure": "Code of Civil Procedure, 1908",
}

SHORT_ACT_MAP = {
    "ipc": "IPC",
    "bns": "BNS",
    "crpc": "CrPC",
    "bnss": "BNSS",
    "bsa": "BSA",
    "iea": "IEA",
    "cpc": "CPC",
}


def _normalize_act_name(act: str | None) -> str | None:
    """Normalize short act names to full names used in metadata."""
    if not act:
        return None
    lower = act.lower().strip()
    return ACT_ALIASES.get(lower, act)


def _short_act(full_name: str | None) -> str | None:
    """Convert full act name to short form."""
    if not full_name:
        return None
    lower = full_name.lower().strip()
    for short, full in ACT_ALIASES.items():
        if full.lower() == lower:
            return SHORT_ACT_MAP.get(short, full_name)
    return full_name


# ── Rule-based fallback (no NIM call) ───────────────────────────────────

def _rule_based_analysis(query: str) -> QueryAnalysis:
    """
    Fast rule-based query analysis. Used as fallback when NIM is unavailable,
    or to pre-process before NIM call.
    """
    lowered = query.lower()
    analysis = QueryAnalysis()
    analysis.raw_json = {"source": "rule_based"}

    # STEP 0: Pre-detect "now Section X" / "corresponds to Section X" patterns
    # This must happen BEFORE source section detection to avoid regex crossover
    target_section_hint = None
    m = re.search(r"\bnow\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
    if m:
        target_section_hint = m.group(1)
    else:
        m = re.search(r"\bcorresponds?\s+to\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
        if m:
            target_section_hint = m.group(1)
        else:
            m = re.search(r"\bequivalent\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
            if m:
                target_section_hint = m.group(1)

    # Concept mapping: natural language -> legal concepts + acts
    # This helps when users describe situations in plain English
    CONCEPT_MAP = [
        (r"in.?laws?.*demand|dowry.*demand|demanding.*money.*marriage|bride.*burn",
         ["dowry", "cruelty", "498A", "maintenance"],
         ["Indian Penal Code, 1860", "Bharatiya Nyaya Sanhita, 2023"]),
        (r"domestic\s+violence|husband.*beat|wife.*abuse",
         ["domestic violence", "cruelty", "498A"],
         ["Indian Penal Code, 1860", "Protection of Women from Domestic Violence Act, 2005"]),
        (r"employer.*not\s+pay|wages.*unpaid|salary.*pending|unpaid\s+wages",
         ["wages", "employer", "industrial dispute", "labour court"],
         ["Industrial Disputes Act, 1947"]),
        (r"minor.*contract|child.*agreement|under\s+18.*contract",
         ["minor", "contract", "void", "Section 10"],
         ["Indian Contract Act, 1872"]),
        (r"drunk\s+driv|drink.*drive|alcohol.*driv|dwi|dui",
         ["drunk driving", "Motor Vehicles Act", "Section 185", "penalty"],
         ["Motor Vehicles Act, 1988"]),
        (r"inheritance.*will|intestate|die.*without\s+will|succession.*hindu",
         ["intestate", "Hindu Succession Act", "heir", "coparcenary"],
         ["Hindu Succession Act, 1956"]),
        (r"accused.*right|right.*accused|police.*interrogat|arrested.*right|right.*interrogat",
         ["accused", "rights", "police", "legal counsel", "advocate", "Section 41D", "BNSS"],
         ["Code of Criminal Procedure, 1973", "Bharatiya Nagarik Suraksha Sanhita, 2023"]),
        (r"confession.*police|police.*confession|admissib.*confession",
         ["confession", "police", "admissible", "Section 25", "evidence"],
         ["Indian Evidence Act, 1872", "Bharatiya Sakshya Adhiniyam, 2023"]),
        (r"limitation.*suit|time\s+limit.*sue|filing.*deadline|limitation\s+period",
         ["limitation", "time limit", "3 years", "Limitation Act"],
         ["Limitation Act, 1963"]),
        (r"false.*case|wrongful.*charge|framed.*crime|falsely.*accused|charged.*crime.*didn|didn.*commit",
         ["false", "wrongful", "acquittal", "innocent", "malicious prosecution", "wrongful prosecution"],
         ["Indian Penal Code, 1860", "Bharatiya Nyaya Sanhita, 2023", "Code of Criminal Procedure, 1973"]),
        (r"forged.*sign|signature.*forg|forgery.*document",
         ["forgery", "fraud", "signature", "crime"],
         ["Indian Penal Code, 1860", "Bharatiya Nyaya Sanhita, 2023"]),
        (r"bail.*provisions?|anticipatory.*bail|bail.*application|grant.*bail|default.*bail",
         ["bail", "anticipatory bail", "default bail", "Section 480", "BNSS"],
         ["Code of Criminal Procedure, 1973", "Bharatiya Nagarik Suraksha Sanhita, 2023"]),
        (r"consumer.*rights?|defective.*goods|deficiency.*service|unfair.*trade.*practice",
         ["consumer rights", "defective goods", "deficiency services", "unfair trade", "Section 38", "Consumer Protection Act"],
         ["Consumer Protection Act, 2019"]),
    ]

    detected_concepts = []
    detected_acts_from_concepts = []
    for pattern, concepts, acts in CONCEPT_MAP:
        if re.search(pattern, lowered):
            detected_concepts.extend(concepts)
            detected_acts_from_concepts.extend(acts)
    detected_acts_from_concepts = list(dict.fromkeys(detected_acts_from_concepts))

    # Detect source act
    source_act = None
    source_section = None

    # Pattern: "IPC Section 302" or "Section 302 IPC"
    m = re.search(r"\bipc\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
    if m:
        source_act = "ipc"
        source_section = m.group(1)
    else:
        m = re.search(r"\bsection\s+(\d+[a-z]?)\b[^.]*?\bipc\b", lowered)
        if m:
            source_act = "ipc"
            source_section = m.group(1)

    # Pattern: "BNS Section 101" or "Section 101 BNS"
    if not source_act:
        m = re.search(r"\bbns\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
        if m:
            source_act = "bns"
            source_section = m.group(1)
        else:
            m = re.search(r"\bsection\s+(\d+[a-z]?)\b[^.]*?\bbns\b", lowered)
            if m:
                source_act = "bns"
                source_section = m.group(1)

    # Pattern: "CrPC Section 144" or "Section 144 CrPC"
    # Use [^.]*? instead of .*? to avoid crossing "now section" to wrong number
    if not source_act:
        m = re.search(r"\bcrpc\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
        if m:
            source_act = "crpc"
            source_section = m.group(1)
        else:
            m = re.search(r"\bsection\s+(\d+[a-z]?)\b[^.]*?\bcrpc\b", lowered)
            if m:
                source_act = "crpc"
                source_section = m.group(1)

    # Pattern: "BNSS Section 163" or "Section 163 BNSS"
    if not source_act:
        m = re.search(r"\bbnss\b[^.]*?\bsection\s+(\d+[a-z]?)\b", lowered)
        if m:
            source_act = "bnss"
            source_section = m.group(1)
        else:
            m = re.search(r"\bsection\s+(\d+[a-z]?)\b[^.]*?\bbnss\b", lowered)
            if m:
                source_act = "bnss"
                source_section = m.group(1)

    # Pattern: just "Section 302" without act
    if not source_section:
        m = re.search(r"\bsection\s+(\d+[a-z]?)\b", lowered)
        if m:
            source_section = m.group(1)

    # Fix: if source_section == target_section_hint, the regex crossed "now section"
    # Find the actual source section (the OTHER section number in the query)
    if source_section and target_section_hint and source_section == target_section_hint:
        all_sections = re.findall(r"\bsection\s+(\d+[a-z]?)\b", lowered)
        for s in all_sections:
            if s != target_section_hint:
                source_section = s
                break

    # Detect ALL act names mentioned in the query (not just source act)
    detected_acts = []
    ACT_PATTERNS = [
        (r"\bipc\b|\bindian penal code\b", "Indian Penal Code, 1860"),
        (r"\bbns\b|\bbharatiya nyaya sanhita\b", "Bharatiya Nyaya Sanhita, 2023"),
        (r"\bcrpc\b|\bcode of criminal procedure\b", "Code of Criminal Procedure, 1973"),
        (r"\bbnss\b|\bbharatiya nagarik suraksha sanhita\b", "Bharatiya Nagarik Suraksha Sanhita, 2023"),
        (r"\bbsa\b|\bbharatiya sakshya adhiniyam\b", "Bharatiya Sakshya Adhiniyam, 2023"),
        (r"\biea\b|\bindian evidence act\b|\bevidence act\b", "Indian Evidence Act, 1872"),
        (r"\bcpc\b|\bcode of civil procedure\b", "Code of Civil Procedure, 1908"),
        (r"\bconsumer protection\b", "Consumer Protection Act, 2019"),
        (r"\bndps\b|\bnarcotic drugs\b", "Narcotic Drugs and Psychotropic Substances Act, 1985"),
        (r"\btransfer of property\b", "Transfer of Property Act, 1882"),
        (r"\bconstitution\b", "Constitution of India"),
        (r"\bindian contract act\b", "Indian Contract Act, 1872"),
        (r"\bhindu marriage\b", "Hindu Marriage Act, 1955"),
        (r"\bhindu succession\b", "Hindu Succession Act, 1956"),
        (r"\bmotor vehicles\b", "Motor Vehicles Act, 1988"),
        (r"\bindustrial disputes\b", "Industrial Disputes Act, 1947"),
        (r"\blimitation act\b", "Limitation Act, 1963"),
        (r"\bnegotiable instruments\b|\bni act\b", "Negotiable Instruments Act, 1881"),
        (r"\barbitration\b", "Arbitration and Conciliation Act, 1996"),
        (r"\bcopyright act\b", "Copyright Act, 1957"),
        (r"\bcompetition act\b", "Competition Act, 2002"),
    ]
    for pattern, act_name in ACT_PATTERNS:
        if re.search(pattern, lowered):
            detected_acts.append(act_name)

    # Detect cross-act intent
    cross_act_keywords = [
        "equivalent", "counterpart", "replaced by", "corresponding",
        "new section", "old section", "was section", "now section",
        "bns equivalent", "ipc equivalent", "mapped to", "corresponds to",
        "compare", "comparison", "difference between", "vs", "versus",
    ]
    is_cross_act = any(kw in lowered for kw in cross_act_keywords)

    # Also detect if both IPC and BNS are mentioned (implicit comparison)
    mentions_ipc = "ipc" in lowered or "indian penal code" in lowered
    mentions_bns = "bns" in lowered or "bharatiya nyaya sanhita" in lowered
    if mentions_ipc and mentions_bns:
        is_cross_act = True

    # Also detect CrPC→BNSS cross-act
    mentions_crpc = "crpc" in lowered or "code of criminal procedure" in lowered
    mentions_bnss = "bnss" in lowered or "bharatiya nagarik suraksha sanhita" in lowered
    if mentions_crpc and mentions_bnss:
        is_cross_act = True

    if is_cross_act and source_act and source_section:
        analysis.intent = "cross_act_mapping"
        analysis.source_act = _normalize_act_name(source_act)
        analysis.source_section = source_section

        # Look up mapping
        if source_act == "ipc":
            mapping = IPC_TO_BNS.get(source_section, {})
            target_section = mapping.get("new")
            if target_section:
                analysis.target_act = "Bharatiya Nyaya Sanhita, 2023"
                analysis.target_section = target_section
                analysis.mapping_info = f"IPC {source_section} to BNS {target_section} ({mapping.get('name', '')})"
                analysis.confidence = 0.95
            else:
                analysis.confidence = 0.6
        elif source_act == "bns":
            ipc_sec = BNS_TO_IPC.get(source_section)
            if ipc_sec:
                analysis.target_act = "Indian Penal Code, 1860"
                analysis.target_section = ipc_sec
                analysis.mapping_info = f"BNS {source_section} to IPC {ipc_sec}"
                analysis.confidence = 0.90
            else:
                analysis.confidence = 0.5
        elif source_act == "crpc":
            # CrPC -> BNSS: use target_section_hint if available
            if target_section_hint:
                analysis.target_act = "Bharatiya Nagarik Suraksha Sanhita, 2023"
                analysis.target_section = target_section_hint
                analysis.mapping_info = f"CrPC {source_section} to BNSS {target_section_hint}"
                analysis.confidence = 0.90
            else:
                analysis.confidence = 0.6
        elif source_act == "bnss":
            if target_section_hint:
                analysis.target_act = "Code of Criminal Procedure, 1973"
                analysis.target_section = target_section_hint
                analysis.mapping_info = f"BNSS {source_section} to CrPC {target_section_hint}"
                analysis.confidence = 0.90
            else:
                analysis.confidence = 0.5

        # Build metadata filters for BOTH acts (include both source and target sections)
        sections = [source_section]
        if analysis.target_section:
            sections.append(analysis.target_section)
        elif target_section_hint:
            # User explicitly mentioned a target section ("now Section 163")
            sections.append(target_section_hint)
            analysis.target_section = target_section_hint
        filters = {"section_number": sections}
        act_names = []
        if analysis.source_act:
            act_names.append(ACT_ALIASES.get(source_act.lower(), source_act))
        if analysis.target_act:
            act_names.append(analysis.target_act)
        if act_names:
            filters["act_name"] = act_names
        analysis.metadata_filters = filters

        # Build rewritten queries for both acts
        source_full = ACT_ALIASES.get(source_act.lower(), source_act) if source_act else None
        rewritten = []
        if source_full and source_section:
            rewritten.append(f"Section {source_section} {SHORT_ACT_MAP.get(source_act.lower(), source_act)} {(' '.join(analysis.legal_concepts)) if analysis.legal_concepts else ''}")
        if analysis.target_act and analysis.target_section:
            target_short = _short_act(analysis.target_act)
            rewritten.append(f"Section {analysis.target_section} {target_short} {(' '.join(analysis.legal_concepts)) if analysis.legal_concepts else ''}")
        if not rewritten:
            rewritten.append(query)
        analysis.rewritten_queries = rewritten

        analysis.search_strategy = "filtered_dual_act"

    elif source_section:
        analysis.intent = "section_lookup"
        analysis.source_section = source_section
        if source_act:
            analysis.source_act = _normalize_act_name(source_act)
            full_name = ACT_ALIASES.get(source_act.lower(), source_act)
            analysis.metadata_filters = {
                "section_number": [source_section],
                "act_name": [full_name],
            }
            analysis.search_strategy = "filtered_single_act"
        elif detected_acts:
            # Section without explicit act — use detected acts from query context
            analysis.metadata_filters = {
                "section_number": [source_section],
                "act_name": detected_acts,
            }
            analysis.search_strategy = "filtered_single_act"
        else:
            analysis.metadata_filters = {"section_number": [source_section]}
            analysis.search_strategy = "filtered_single_act"
        analysis.rewritten_queries = [query]
        analysis.confidence = 0.7

    else:
        # No section found — concept query
        if detected_concepts:
            analysis.intent = "concept_search"
            analysis.legal_concepts = detected_concepts
            analysis.rewritten_queries = [f"{' '.join(detected_concepts)} {query}"]
            analysis.confidence = 0.65
            # Only use filtered search when the QUERY TEXT explicitly mentions an act
            # (not when concept mapping infers acts from natural language)
            query_has_act = bool(re.search(
                r"\b(ipc|bns|crpc|bnss|bsa|cpc|act)\b"
                r"|indian penal code|bharatiya nyaya sanhita"
                r"|code of criminal procedure|bharatiya nagarik suraksha sanhita"
                r"|bharatiya sakshya adhiniyam|indian evidence act"
                r"|transfer of property act|consumer protection act"
                r"|ndps|narcotic|motor vehicles act|hindu succession"
                r"|indian contract act|limitation act",
                lowered
            ))
            if query_has_act and detected_acts_from_concepts:
                analysis.metadata_filters = {"act_name": detected_acts_from_concepts}
                analysis.search_strategy = "filtered_single_act"
            else:
                analysis.search_strategy = "unfiltered_broad"
        else:
            analysis.intent = "concept_search"
            analysis.rewritten_queries = [query]
            analysis.search_strategy = "unfiltered_broad"
            analysis.confidence = 0.5

    return analysis


# ── NIM-based analysis ──────────────────────────────────────────────────

def _nim_analysis(query: str) -> QueryAnalysis | None:
    """
    Use Nemotron Nano 8B to analyze the query.
    Returns QueryAnalysis or None if NIM fails.
    """
    try:
        from core.nim_llm import get_nim_llm, NIM_MODELS

        nim = get_nim_llm()
        model = NIM_MODELS.get("query_intelligence", NIM_MODELS.get("router"))

        # Build messages with mapping context
        mapping_context = _build_mapping_context()

        messages = [
            {"role": "system", "content": QI_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Available acts in corpus:\n{mapping_context}\n\nAnalyze this query:\n{query}",
            },
        ]

        raw = nim.chat(
            messages,
            temperature=0.0,
            max_tokens=800,
            response_format={"type": "json_object"},
            model=model,
        )

        data = json.loads(raw)
        return _parse_nim_output(data, query)

    except Exception as e:
        logger.warning("QI NIM analysis failed: %s", e)
        return None


def _build_mapping_context() -> str:
    """Build a compact mapping context string for the NIM prompt."""
    lines = []
    for act in KNOWN_ACTS[:20]:  # Top 20 acts
        lines.append(f"- {act}")
    lines.append("")
    lines.append("IPC→BNS key cross-references (IPC section → BNS section):")
    # Include the most important 50 mappings
    important = ["302", "304", "304B", "376", "379", "303", "323", "498A",
                 "506", "420", "406", "354", "299", "300", "307", "308",
                 "392", "425", "441", "463", "120A", "120B", "34", "147",
                 "148", "149", "509", "375", "301", "395", "493", "498"]
    for ipc_sec in important:
        data = IPC_TO_BNS.get(ipc_sec, {})
        if data:
            lines.append(f"  IPC {ipc_sec} to BNS {data['new']} ({data.get('name', '')})")
    return "\n".join(lines)


def _parse_nim_output(data: dict, query: str) -> QueryAnalysis:
    """Parse NIM JSON output into QueryAnalysis."""
    analysis = QueryAnalysis()
    analysis.raw_json = data

    analysis.intent = data.get("intent", "general_legal")
    analysis.confidence = float(data.get("confidence", 0.5))
    analysis.source_act = _normalize_act_name(data.get("source_act"))
    analysis.source_section = data.get("source_section")
    analysis.target_act = _normalize_act_name(data.get("target_act"))
    analysis.target_section = data.get("target_section")
    analysis.legal_concepts = data.get("legal_concepts", [])
    analysis.rewritten_queries = data.get("rewritten_queries", [query])
    analysis.search_strategy = data.get("search_strategy", "unfiltered_broad")

    # Build metadata filters
    meta = data.get("metadata_filters", {})
    if meta:
        filters = {}
        if meta.get("act_name"):
            filters["act_name"] = [_normalize_act_name(a) or a for a in meta["act_name"]]
        if meta.get("section_number"):
            filters["section_number"] = meta["section_number"]
        analysis.metadata_filters = filters

    # If cross-act mapping and NIM didn't provide target, look it up
    if analysis.intent == "cross_act_mapping" and analysis.source_section and not analysis.target_section:
        if analysis.source_act and "ipc" in (analysis.source_act or "").lower():
            mapping = IPC_TO_BNS.get(analysis.source_section, {})
            if mapping:
                analysis.target_section = mapping.get("new")
                analysis.target_act = "Bharatiya Nyaya Sanhita, 2023"
                analysis.mapping_info = f"IPC {analysis.source_section} to BNS {analysis.target_section} ({mapping.get('name', '')})"

    # Ensure rewritten_queries has at least the original query
    if not analysis.rewritten_queries:
        analysis.rewritten_queries = [query]

    return analysis


# ── Public API ──────────────────────────────────────────────────────────

def analyze_query(query: str, use_nim: bool = True) -> QueryAnalysis:
    """
    Analyze a user query and return structured QueryAnalysis.

    Flow:
    1. Run rule-based analysis (fast, always works)
    2. If NIM is available and query is complex, enhance with NIM analysis
    3. Merge results (NIM overrides rules where confident)
    """
    # Always start with rule-based (fast, reliable for entity extraction)
    rule_result = _rule_based_analysis(query)

    # If NIM is enabled and the query looks complex, try NIM
    if use_nim:
        nim_result = _nim_analysis(query)
        if nim_result and nim_result.confidence >= rule_result.confidence:
            # NIM is more confident — use it, but merge metadata from rules
            if not nim_result.metadata_filters and rule_result.metadata_filters:
                nim_result.metadata_filters = rule_result.metadata_filters
            if not nim_result.target_section and rule_result.target_section:
                nim_result.target_section = rule_result.target_section
                nim_result.target_act = rule_result.target_act
            if rule_result.mapping_info:
                nim_result.mapping_info = rule_result.mapping_info
            return nim_result

    return rule_result


def get_mapping_info(source_act: str, source_section: str) -> dict | None:
    """
    Look up cross-act mapping for a given section.
    Returns dict with 'target_act', 'target_section', 'name' or None.
    """
    act_lower = source_act.lower().strip()

    if "ipc" in act_lower:
        data = IPC_TO_BNS.get(source_section)
        if data:
            return {
                "target_act": "Bharatiya Nyaya Sanhita, 2023",
                "target_section": data["new"],
                "name": data.get("name", ""),
                "note": data.get("note", ""),
            }

    if "bns" in act_lower:
        ipc_sec = BNS_TO_IPC.get(source_section)
        if ipc_sec:
            ipc_data = IPC_TO_BNS.get(ipc_sec, {})
            return {
                "target_act": "Indian Penal Code, 1860",
                "target_section": ipc_sec,
                "name": ipc_data.get("name", ""),
                "note": ipc_data.get("note", ""),
            }

    return None
