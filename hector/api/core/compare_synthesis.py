"""Grounded compare synthesis.

Turns the two fetched compare provisions into a fixed-aspect comparison
table plus a short grounded message, using a small NIM instruct model.

Groundedness contract:
- the model sees ONLY the provisions chunk (system prompt forbids outside
  knowledge; anything not stated in the text must be "-");
- validate_synthesis() re-checks the output offline (exact aspect list,
  every act+section reference must occur in the chunk, length caps);
- any failure returns None and the caller falls back to the plain
  two-panel compare response.
"""

from __future__ import annotations

import logging
import os
import queue
import re
import threading
import time

from core.nim_llm import NIM_MODELS, _split_models, call_with_deadline, get_nim_llm

logger = logging.getLogger("hector.compare_synthesis")

# Which act each act compares against. IPC <-> BNS is the only live pair
# (its crosswalk lives in core/mapping.json); the CRPC/BNSS and IEA/BSA
# slots are reserved and activate once those books are ingested and a
# crosswalk table exists. An act absent from this dict gets no synthesis.
PAIR_COUNTERPART: dict[str, str] = {
    "IPC": "BNS",
    "BNS": "IPC",
    "CRPC": "BNSS",
    "BNSS": "CRPC",
    "IEA": "BSA",
    "BSA": "IEA",
}

# Fixed comparison aspects (rows) for the substantive-law IPC/BNS pair.
# Procedural pairs get their own list when they go live.
ASPECTS_SUBSTANTIVE = [
    "Provision",
    "Offence / definition",
    "Punishment",
    "Intent / exceptions",
    "Notes",
]

_ASPECTS_BY_PAIR = {
    frozenset(("IPC", "BNS")): ASPECTS_SUBSTANTIVE,
}

_CELL_MAX_CHARS = 400
_MESSAGE_MAX_CHARS = 420
_SIDE_TEXT_MAX_CHARS = 3500

_SECTION_REF_RE = re.compile(
    r"\b(IPC|BNS|CRPC|BNSS|IEA|BSA|CPC)\s+(\d{1,4}[A-Z]?)\b"
)

_SYSTEM_TEMPLATE = """\
You compare two provisions of Indian law, side by side.

You receive exactly one user message with three parts:
[REQUESTED] act, section, title and text of the provision to analyse
[COUNTERPART] act, section, title and text of its mapped counterpart
[MAPPING NOTE] how the two provisions relate (may be empty)

Strict rules:
1. Use ONLY facts present in the provided text. Never use outside knowledge.
2. If the text does not state a value for a cell, write exactly a dash.
3. Reference provisions only in the form "ACT NUMBER" (example: IPC 302),
   and only when that pair appears in the provided text.
4. Answer with ONE JSON object and nothing else:
   {{"rows": [{{"aspect": "...", "requested": "...", "counterpart": "..."}}],
    "message": "..."}}
5. "rows" must contain EXACTLY these aspects, in this order: {aspects}
   - "Provision": ACT NUMBER and title for each side.
   - "Offence / definition": what the text says the offence or conduct is.
   - "Punishment": the punishment stated in the text.
   - "Intent / exceptions": mens rea or exceptions stated in the text.
   - "Notes": how the two texts differ or relate, strictly from the texts
     and the mapping note.
6. Each cell: at most 45 words. "message": exactly two short sentences
   (at most 45 words) summarising the comparison, grounded in the text.
"""


def _side_text(items: list[dict]) -> tuple[str, str]:
    """(title, joined text) for one side's selected raw panel items."""
    title = ""
    parts: list[str] = []
    budget = _SIDE_TEXT_MAX_CHARS
    for item in items or []:
        meta = item.get("metadata") or {}
        if not title:
            title = str(meta.get("section_title") or "").strip()
        text = " ".join(str(item.get("document") or "").split())
        if not text:
            continue
        if len(text) > budget:
            text = text[:budget].rstrip() + " ...[truncated]"
        budget -= len(text)
        parts.append(text)
        if budget <= 0:
            break
    return title, "\n".join(parts)


def build_provisions_chunk(
    requested_act: str,
    requested_section: str,
    requested_items: list[dict],
    counterpart_act: str,
    counterpart_section: str,
    counterpart_items: list[dict],
    note: str | None,
) -> str:
    """Compact, deterministic serialization of both sides for the model."""
    req_title, req_text = _side_text(requested_items)
    cp_title, cp_text = _side_text(counterpart_items)
    return (
        f"[REQUESTED] act={requested_act} section={requested_section} "
        f"title={req_title}\n{req_text}\n"
        "---\n"
        f"[COUNTERPART] act={counterpart_act} section={counterpart_section} "
        f"title={cp_title}\n{cp_text}\n"
        "---\n"
        f"[MAPPING NOTE] {note or ''}"
    )


def validate_synthesis(
    data, aspects: list[str], allowed_refs: set[tuple[str, str]]
) -> tuple[bool, str]:
    """Offline groundedness check. Returns (ok, reason).

    allowed_refs is the set of (ACT, SECTION) pairs that occur in the fed
    chunk; any act+section the model mentions outside it rejects the whole
    synthesis.
    """
    if not isinstance(data, dict):
        return False, "not-object"
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != len(aspects):
        return False, "row-count"
    texts: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return False, "row-type"
        if row.get("aspect") != aspects[index]:
            return False, "aspect-order"
        for side in ("requested", "counterpart"):
            cell = row.get(side)
            if not isinstance(cell, str) or not cell.strip():
                return False, "cell-missing"
            if len(cell) > _CELL_MAX_CHARS:
                return False, "cell-too-long"
            texts.append(cell)
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return False, "message-missing"
    if len(message) > _MESSAGE_MAX_CHARS:
        return False, "message-too-long"
    texts.append(message)
    for act, section in _SECTION_REF_RE.findall(" ".join(texts)):
        if (act, section) not in allowed_refs:
            return False, f"ungrounded-ref:{act} {section}"
    return True, "ok"


def synthesize_comparison(
    *,
    requested_act: str,
    requested_section: str,
    requested_items: list[dict],
    counterpart_act: str,
    counterpart_section: str,
    counterpart_items: list[dict],
    note: str | None = None,
) -> dict | None:
    """Model + validation. Returns {"rows", "message"} or None (caller
    falls back to plain panels)."""
    if os.getenv("HECTOR_COMPARE_DISABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return None
    aspects = _ASPECTS_BY_PAIR.get(
        frozenset((requested_act.upper(), counterpart_act.upper()))
    )
    if aspects is None:
        logger.debug(
            "compare synthesis: no aspect schema for pair %s/%s",
            requested_act,
            counterpart_act,
        )
        return None

    chunk = build_provisions_chunk(
        requested_act,
        requested_section,
        requested_items,
        counterpart_act,
        counterpart_section,
        counterpart_items,
        note,
    )
    allowed = set(_SECTION_REF_RE.findall(chunk))
    allowed.add((str(requested_act).upper(), str(requested_section).upper()))
    allowed.add((str(counterpart_act).upper(), str(counterpart_section).upper()))

    system = _SYSTEM_TEMPLATE.format(
        aspects=", ".join(f'"{a}"' for a in aspects)
    )
    model = NIM_MODELS.get("compare")
    # Wall-clock budget for the WHOLE synthesis (was 3s for one call —
    # way too tight). 18s measured basis (2026-10-06): these are REASONING
    # models, so a compare-shaped JSON call runs ~10-12s under load (a
    # sequential nano call blew a 12s budget at exactly 12.0s), and the
    # 503-retry storms make it worse. Candidates race in parallel (below),
    # so this is never multiplied by the number of candidates; the common
    # success path returns as soon as the first candidate answers.
    deadline_s = float(os.getenv("HECTOR_COMPARE_DEADLINE_S", "18") or 18)
    candidates = [m for m in _split_models(model) if m]
    if not candidates:
        logger.warning("compare synthesis: no model candidates configured")
        return None
    try:
        client = get_nim_llm()
    except Exception as exc:
        logger.warning("compare synthesis unavailable (%s)", exc)
        return None

    # The model pools congest independently (measured 2026-10-06: nano
    # returns 503 "worker limit reached" while ultra hangs >20s, and the
    # other way around), so candidates are RACED on daemon threads and the
    # first output passing validate_synthesis wins. Losers are abandoned:
    # each inner call_with_deadline stops its own worker, and daemon
    # threads can never block the response or interpreter shutdown.
    results: queue.Queue = queue.Queue()

    def _attempt(candidate: str) -> None:
        try:
            # max_attempts=1: this call is abandoned at deadline_s by the
            # outer call_with_deadline — with the default retry chain the
            # abandoned thread would keep firing NEW NIM requests for
            # minutes (observed 2026-10-06), piling load onto the already
            # congested worker pool. The parallel race below IS the
            # redundancy; SDK-level fast-503 retries still apply.
            payload = call_with_deadline(
                lambda: client.chat_json(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": chunk},
                    ],
                    max_tokens=900,
                    model=candidate,
                    max_attempts=1,
                ),
                deadline_s,
            )
            results.put((candidate, payload, None))
        except Exception as exc:  # noqa: BLE001 - reported as a candidate failure
            results.put((candidate, None, exc))

    for candidate in candidates:
        threading.Thread(
            target=_attempt,
            args=(candidate,),
            daemon=True,
            name="compare-synthesis",
        ).start()

    # One overall bound: results arrive in parallel, so the slowest
    # possible outcome is ~one deadline (+ small grace), not deadline x N.
    give_up = time.monotonic() + deadline_s + 2.0
    pending = len(candidates)
    while pending > 0:
        remaining = give_up - time.monotonic()
        if remaining <= 0:
            break
        try:
            candidate, data, exc = results.get(timeout=remaining)
        except queue.Empty:
            break
        pending -= 1
        if exc is not None:
            logger.warning(
                "compare synthesis: %s unavailable (%s)", candidate, exc
            )
            continue
        ok, reason = validate_synthesis(data, aspects, allowed)
        if ok:
            return {"rows": data["rows"], "message": data["message"]}
        logger.warning("compare synthesis: %s rejected (%s)", candidate, reason)
    if pending > 0:
        logger.warning(
            "compare synthesis: no candidate answered within %.0fs", deadline_s
        )
    return None
