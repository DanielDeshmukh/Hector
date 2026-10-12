"""gold_common.py - shared helpers for gen_gold_*.py question generation."""
from __future__ import annotations

import re

# Titles this short / generic make the number-free question ambiguous:
# the topic word ("procedure", "punishment", "repeal") appears in the text
# of hundreds of sections, so retrieval cannot disambiguate.
SHORT_TITLE_WORDS = 3

# Sections whose title is so generic that even chapter qualification fails
# retrieval. Maps (act_prefix, section_number) -> more specific topic phrase.
# The phrase is derived from the section body so the number-free question
# becomes well-posed.
CUSTOM_TOPICS: dict[tuple[str, str], str] = {
    ("ipc", "311"): "punishment for thuggery",
    ("bnss", "145"): "procedure for maintenance proceedings",
    ("bnss", "531"): "repeal of the old Code of Criminal Procedure and savings",
    ("crpc", "126"): "procedure for maintenance proceedings",
    ("crpc", "484"): "repeal of the old Criminal Procedure Code and savings",
}


def qualify_title(title: str, chapter: str, dup_titles: set[str],
                  act_prefix: str = "", section_number: str = "") -> str:
    """Return the topic string for number-free questions.

    Uses a custom topic when the section is in CUSTOM_TOPICS (ultra-generic
    title). Otherwise appends chapter context when the title is a duplicate,
    or is so short that the bare topic word is ambiguous across the act.
    """
    custom = CUSTOM_TOPICS.get((act_prefix, section_number))
    if custom:
        return custom
    t = re.sub(r"\s+", " ", title).lower().rstrip(".")
    words = t.split()
    is_short = len(words) <= SHORT_TITLE_WORDS
    is_dup = t in dup_titles
    if (is_short or is_dup) and chapter:
        ch = re.sub(r"\s+", " ", chapter).strip()
        t = f"{t} in {ch}"
    return t


def collect_dup_titles(sections: list[dict]) -> set[str]:
    """Titles shared by 2+ sections (lowercased, trailing dot stripped)."""
    from collections import Counter
    counts = Counter(
        (r.get("title") or "").strip().lower().rstrip(".")
        for r in sections if (r.get("title") or "").strip()
    )
    return {t for t, c in counts.items() if c > 1}
