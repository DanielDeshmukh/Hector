"""Act-name coverage for the BNS family and its repealed counterparts.

Every surface form a user can type for BNS/BNSS/BSA (and for the repealed
IPC/CrPC/Indian Evidence Act, plus CPC) must (a) resolve to its canonical
act, (b) carry its section number into the cited-section table, and (c)
never leak a bogus act out of an English word or a bogus section out of an
act year. Both act regexes are built from one alternation, so these tests
also pin that no pattern can drift away from the alias table.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import HectorRouter  # noqa: E402
from data.hybrid_retriever import HectorHybridRetriever  # noqa: E402


@pytest.fixture(scope="module")
def retriever():
    return HectorHybridRetriever.__new__(HectorHybridRetriever)


@pytest.fixture(scope="module")
def router():
    return HectorRouter.__new__(HectorRouter)


def _surfaces(retriever, text):
    return [m.group(0).lower() for m in retriever.ACT_PATTERN.finditer(text)]


def _canonical(retriever, text):
    return [
        retriever.ACT_ALIASES.get(
            re.sub(r"\.", "", surface), "UNMAPPED:" + surface.upper()
        )
        for surface in _surfaces(retriever, text)
    ]


# (surface form, canonical act it must resolve to)
ACT_SURFACES = [
    # --- 2023 family ---
    ("bns", "BNS"),
    ("BNS", "BNS"),
    ("Bharatiya Nyaya Sanhita", "BNS"),
    ("Bharatiya Nyaya Sanhita, 2023", "BNS"),
    ("the Bharatiya Nyaya Sanhita, 2023 (BNS)", "BNS"),
    ("bnss", "BNSS"),
    ("Bharatiya Nagarik Suraksha Sanhita", "BNSS"),
    ("Bharatiya Nagarik Suraksha Sanhita, 2023", "BNSS"),
    ("bsa", "BSA"),
    ("Bharatiya Sakshya Adhiniyam", "BSA"),
    ("Bharatiya Sakshya Adhiniyam, 2023", "BSA"),
    # --- repealed counterparts ---
    ("ipc", "IPC"),
    ("Indian Penal Code", "IPC"),
    ("Indian Penal Code, 1860", "IPC"),
    ("crpc", "CRPC"),
    ("CrPC", "CRPC"),
    ("Code of Criminal Procedure", "CRPC"),
    ("Code of Criminal Procedure, 1973", "CRPC"),
    ("evidence act", "BSA"),
    ("Indian Evidence Act", "BSA"),
    ("Indian Evidence Act, 1872", "BSA"),
    ("iea", "BSA"),
    ("IEA", "BSA"),
    # --- brief-style dotted citations ---
    ("I.P.C.", "IPC"),
    ("I.P.C", "IPC"),
    ("B.N.S.", "BNS"),
    ("B.N.S.S.", "BNSS"),
    ("Cr.P.C.", "CRPC"),
    ("C.R.P.C.", "CRPC"),
    ("B.S.A.", "BSA"),
    ("I.E.A.", "BSA"),
    ("C.P.C.", "CPC"),
    # --- civil (alias keys existed; the full names did not) ---
    ("cpc", "CPC"),
    ("Code of Civil Procedure", "CPC"),
    ("Code of Civil Procedure, 1908", "CPC"),
]

# (text, act that must NOT appear in the parse) - English words and fused
# tokens that contain an act abbreviation as a substring
ACT_LEAKS = [
    ("the package", "IPC"),
    ("discipline", "BNS"),
    ("absa scheme", "BSA"),
    ("bsnl phone", "BSA"),
    ("BNSB helicopter", "BNS"),
    ("supercpc", "CPC"),
    ("RIP contest", "IPC"),
    ("iearn money", "BSA"),
]

# act + bare number must parse the number (and must NOT eat the act year)
ACT_TAGGED_SECTIONS = [
    ("BNS 318", "318", "BNS"),
    ("IPC 420", "420", "IPC"),
    ("bnss 175", "175", "BNSS"),
    ("BSA 22", "22", "BSA"),
    ("IEA 27", "27", "BSA"),
    ("CPC 9", "9", "CPC"),
    ("CrPC 41A", "41A", "CRPC"),
    ("I.P.C. 302", "302", "IPC"),
    ("B.N.S. 103", "103", "BNS"),
    ("B.N.S.S. 175", "175", "BNSS"),
    ("B.S.A. 22", "22", "BSA"),
    ("Indian Penal Code 302", "302", "IPC"),
    ("Bharatiya Nyaya Sanhita 103", "103", "BNS"),
    ("Bharatiya Nagarik Suraksha Sanhita 175", "175", "BNSS"),
]

YEAR_CASES = [
    "Bharatiya Nyaya Sanhita 2023",
    "Bharatiya Nagarik Suraksha Sanhita 2023",
    "Bharatiya Sakshya Adhiniyam 2023",
    "Indian Penal Code 1860",
    "Code of Criminal Procedure 1973",
    "Indian Evidence Act 1872",
    "Code of Civil Procedure 1908",
    "BSA 2023",
    "IPC 1860",
]

# (query, expected section_numbers, expected acts, expected (num, acts) pairs)
FULL_CITATIONS = [
    ("Explain Section 302 of the Bharatiya Nyaya Sanhita, 2023",
     ["302"], ["BNS"], [("302", ["BNS"])]),
    ("Punishment under Section 420 of the Indian Penal Code, 1860",
     ["420"], ["IPC"], [("420", ["IPC"])]),
    ("What is Section 318 of the BNS?",
     ["318"], ["BNS"], [("318", ["BNS"])]),
    # only the CITED act gets the section - attributing both would inject
    # unrelated lookalikes (see _cited_act_sections docstring)
    ("IPC equivalent of BNS 318",
     ["318"], ["IPC", "BNS"], [("318", ["BNS"])]),
    ("difference between BNS 103 and IPC 302",
     ["103", "302"], ["BNS", "IPC"],
     [("103", ["BNS"]), ("302", ["IPC"])]),
    ("I.P.C. Section 302 punishment",
     ["302"], ["IPC"], [("302", ["IPC"])]),
    ("B.N.S.S. Section 175 procedure",
     ["175"], ["BNSS"], [("175", ["BNSS"])]),
    ("IEA Section 27 admissibility",
     ["27"], ["BSA"], [("27", ["BSA"])]),
    ("Section 27 of the Indian Evidence Act, 1872",
     ["27"], ["BSA"], [("27", ["BSA"])]),
    ("CrPC Section 41A arrest",
     ["41a"], ["CRPC"], [("41A", ["CRPC"])]),
    ("Cr.P.C. Section 41A arrest",
     ["41a"], ["CRPC"], [("41A", ["CRPC"])]),
    ("C.R.P.C. Section 41A arrest",
     ["41a"], ["CRPC"], [("41A", ["CRPC"])]),
    ("Code of Criminal Procedure, 1973 Section 98",
     ["98"], ["CRPC"], [("98", ["CRPC"])]),
    ("Code of Civil Procedure, 1908 Section 9",
     ["9"], ["CPC"], [("9", ["CPC"])]),
    ("B.S.A. 22 expert evidence",
     ["22"], ["BSA"], [("22", ["BSA"])]),
    ("Bharatiya Nyaya Sanhita 2023 Section 103",
     ["103"], ["BNS"], [("103", ["BNS"])]),
    ("Indian Penal Code 1860 Section 302",
     ["302"], ["IPC"], [("302", ["IPC"])]),
]

# queries the router must classify as LEGAL_RESEARCH without a "section N"
# keyword to lean on
ROUTER_ACT_GATES = [
    "BSA 22",
    "IEA 27",
    "CPC 9",
    "I.P.C. 420",
    "B.N.S. 103",
    "B.N.S.S. 175",
    "Cr.P.C. 41A",
    "indian penal code 420",
    "indian evidence act 27",
    "Code of Civil Procedure 1908",
    "bharatiya sakshya adhiniyam 22",
]


@pytest.mark.parametrize("text,canonical", ACT_SURFACES)
def test_act_surface_resolves_to_canonical(retriever, text, canonical):
    assert canonical in _canonical(retriever, text), (
        f"{text!r} did not resolve to {canonical}: "
        f"surfaces={_surfaces(retriever, text)}"
    )


@pytest.mark.parametrize("text,forbidden", ACT_LEAKS)
def test_english_word_never_matches_an_act(retriever, text, forbidden):
    assert forbidden not in _canonical(retriever, text), (
        f"{text!r} leaked act {forbidden}: surfaces={_surfaces(retriever, text)}"
    )


@pytest.mark.parametrize("text,number,act", ACT_TAGGED_SECTIONS)
def test_act_tagged_bare_number_parses(retriever, text, number, act):
    parsed = [n.upper() for n in retriever.ACT_SECTION_PATTERN.findall(text)]
    assert number.upper() in parsed, f"{text!r} parsed {parsed}, missing {number}"
    assert act in _canonical(retriever, text)


@pytest.mark.parametrize("text", YEAR_CASES)
def test_act_year_never_parses_as_section(retriever, text):
    assert retriever.ACT_SECTION_PATTERN.findall(text) == [], (
        f"{text!r} parsed its act year as a section number"
    )


@pytest.mark.parametrize(
    "query,sections,acts,cited", FULL_CITATIONS, ids=[c[0] for c in FULL_CITATIONS]
)
def test_full_citation_extracts_sections_and_acts(
    retriever, query, sections, acts, cited
):
    legal_query = retriever._parse_query(query)
    assert legal_query["section_numbers"] == sections
    assert legal_query["acts"] == acts
    assert legal_query["has_legal_citation"] is True
    got = [(num, list(pair_acts)) for num, pair_acts in
           retriever._cited_act_sections(query, legal_query)]
    assert got == [(num, list(pair_acts)) for num, pair_acts in cited]


def test_dotted_form_matches_flat_form(retriever):
    for dotted, flat in [
        ("I.P.C. Section 302", "IPC Section 302"),
        ("B.N.S.S. 175", "bnss 175"),
        ("B.S.A. 22", "bsa 22"),
        ("I.E.A. 27", "iea 27"),
        ("Cr.P.C. 41A", "crpc 41A"),
        ("C.R.P.C. 41A", "crpc 41A"),
    ]:
        assert retriever._parse_query(dotted)["acts"] == retriever._parse_query(flat)["acts"]
        assert (
            retriever._parse_query(dotted)["section_numbers"]
            == retriever._parse_query(flat)["section_numbers"]
        )


def test_bns_family_never_confused(retriever):
    for text in ["B.N.S.S. 175", "bnss 175", "Bharatiya Nagarik Suraksha Sanhita 175"]:
        assert _canonical(retriever, text) == ["BNSS"]
    for text in ["B.N.S. 103", "bns 103", "Bharatiya Nyaya Sanhita 103"]:
        assert _canonical(retriever, text) == ["BNS"]


def test_both_patterns_share_one_act_alternation():
    for pattern in (
        HectorHybridRetriever.ACT_PATTERN,
        HectorHybridRetriever.ACT_SECTION_PATTERN,
    ):
        assert HectorHybridRetriever._ACT_NAME_ALTERNATION in pattern.pattern, (
            "act pattern drifts from the shared alternation"
        )


def test_every_pattern_alias_maps_to_exact_act_names():
    unmapped = [
        surface
        for surface in HectorHybridRetriever.ACT_ALIASES
        if surface not in HectorHybridRetriever.ACT_TO_EXACT
    ]
    assert unmapped == [], f"alias without exact act names: {unmapped}"


@pytest.mark.parametrize("query", ROUTER_ACT_GATES)
def test_router_routes_bare_act_references_to_legal(router, query):
    result = router._route_with_rules(query)
    assert result["route"] == "LEGAL_RESEARCH", (
        f"{query!r} routed to {result['route']}"
    )
