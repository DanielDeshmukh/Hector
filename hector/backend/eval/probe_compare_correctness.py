"""Correctness probe for the frontend's IPC<->BNS compare section (POST /compare).

The three passing gates (recall 1.0000 / grounded 0.9944 / fabricated 1.0000)
were measured on IPC-only gold and say nothing about compare. services.compare()
issues two unrestricted hybrid searches ("Section N ACT") with no act/section
filter - retrieval only guarantees a 50% same-act promotion floor - so a panel
headed "BNS Results" can contain IPC cards (visible via bookTitle) and a query
for section 302 can surface a neighbouring section.

This runs the real HectorApiService.compare() (production mapping + warm
retriever) over a seeded sample and measures, per panel:

    top1_act_ok      top-1 card belongs to the requested act
    top1_sec_ok      top-1 card is the exact requested section
    act_pure         all 3 cards belong to the requested act
    sec_exact        all 3 cards are the exact requested section
    nonempty         at least one card returned

    python probe_compare_correctness.py            # 20 IPC + 20 BNS
    COMPARE_N=40 python probe_compare_correctness.py
"""

import json
import os
import random
import statistics
import sys
import time
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402
from api.schemas import CompareRequest  # noqa: E402
from api.services import HectorApiService  # noqa: E402

SAMPLE_SEED = int(os.getenv("COMPARE_SAMPLE_SEED", "20261013"))
PER_ACT = int(os.getenv("COMPARE_N", "20"))


def hit_act(hit) -> str:
    """Normalize a SearchHit to 'IPC'/'BNS'/'' for act comparison."""
    raw = str(hit.act or "").strip().upper()
    if raw in ("IPC", "BNS"):
        return raw
    meta = hit.metadata or {}
    blob = " ".join(
        str(meta.get(k, "")) for k in ("real_act_name", "act_name", "act", "source")
    ).upper()
    if "BHARATIYA NYAYA" in blob:
        return "BNS"
    if "INDIAN PENAL" in blob or "IPC" in blob:
        return "IPC"
    return raw or "?"


def hit_section(hit) -> str:
    meta = hit.metadata or {}
    for key in ("section_number", "section"):
        val = meta.get(key)
        if val not in (None, ""):
            return str(val).strip().upper()
    return ""


def panel_stats(hits, exp_act, exp_sec):
    acts = [hit_act(h) for h in hits]
    secs = [hit_section(h) for h in hits]
    return {
        "nonempty": bool(hits),
        "top1_act_ok": bool(hits) and acts[0] == exp_act,
        "top1_sec_ok": bool(hits) and secs[0] == exp_sec,
        "act_pure": bool(hits) and all(a == exp_act for a in acts),
        "sec_exact": bool(hits) and all(s == exp_sec for s in secs),
        "acts": acts,
        "secs": secs,
    }


def build_service():
    stack = rge.build_stack()
    legal_map = json.loads(
        (ROOT / "hector" / "api" / "core" / "mapping.json").read_text(encoding="utf-8")
    ).get("IPC_TO_BNS", {})
    # Compare only touches router.legal_map, retriever.search and _to_hit, so
    # skip the full HectorOrchestrator build and wire the production pieces in.
    svc = object.__new__(HectorApiService)
    svc.retriever = stack["retriever"]
    svc.router = types.SimpleNamespace(legal_map=legal_map)
    return svc, legal_map


def instrument_search(ret):
    """Record wall time + last_stage_info.timings_ms for every retrieval call.

    Wraps search(), search_with_metadata_filters(), and (since the 2026-10-04
    fix) search_exact_section() - compare prefers the exact-section path,
    which does one filtered Pinecone query and no cross-encoder rerank.
    """
    calls = []

    def wrap(name, original):
        def recorded(*args, **kwargs):
            t0 = time.perf_counter()
            result = original(*args, **kwargs)
            wall = (time.perf_counter() - t0) * 1000
            info = getattr(ret, "last_stage_info", None) or {}
            calls.append(
                {"via": name, "wall_ms": wall, "timings": dict(info.get("timings_ms") or {})}
            )
            return result

        return recorded

    ret.search = wrap("search", ret.search)
    filtered = getattr(ret, "search_with_metadata_filters", None)
    if filtered is not None:
        ret.search_with_metadata_filters = wrap("filtered", filtered)
    exact = getattr(ret, "search_exact_section", None)
    if exact is not None:
        ret.search_exact_section = wrap("exact", exact)
    return calls


def sample_sections(legal_map):
    rng = random.Random(SAMPLE_SEED)
    ipc = sorted(legal_map, key=lambda s: (len(s), s))
    bns = sorted({str(v.get("new")) for v in legal_map.values() if v.get("new")},
                 key=lambda s: (len(s), s))
    ipc_pick = rng.sample(ipc, min(PER_ACT, len(ipc)))
    bns_pick = rng.sample(bns, min(PER_ACT, len(bns)))
    return [("IPC", s) for s in sorted(ipc_pick)], [("BNS", s) for s in sorted(bns_pick)]


def main():
    print(f"sample seed={SAMPLE_SEED} per_act={PER_ACT}", flush=True)
    svc, legal_map = build_service()
    search_calls = instrument_search(svc.retriever)
    ipc_cases, bns_cases = sample_sections(legal_map)
    cases = ipc_cases + bns_cases
    print(f"cases: {len(cases)} ({len(ipc_cases)} IPC->BNS, {len(bns_cases)} BNS->IPC)"
          f"  mapping entries={len(legal_map)}", flush=True)

    sides = {
        "requested": {"n": 0, "nonempty": 0, "top1_act_ok": 0, "top1_sec_ok": 0,
                      "act_pure": 0, "sec_exact": 0},
        "counterpart": {"n": 0, "nonempty": 0, "top1_act_ok": 0, "top1_sec_ok": 0,
                        "act_pure": 0, "sec_exact": 0},
    }
    mapping_misses, latencies, failures = [], [], []

    for act, sec in cases:
        t0 = time.perf_counter()
        try:
            resp = svc.compare(CompareRequest(section=sec, act=act))
        except Exception as exc:
            print(f"  ERROR {act} {sec}: {type(exc).__name__}: {exc}", flush=True)
            mapping_misses.append((act, sec, f"exception:{type(exc).__name__}"))
            continue
        latencies.append((time.perf_counter() - t0) * 1000)

        # mapping direction check
        if not resp.counterpart_act or not resp.counterpart_section:
            mapping_misses.append((act, sec, "no counterpart in mapping"))

        for name, hits, exp_act, exp_sec in (
            ("requested", resp.requested_results, resp.requested_act,
             str(resp.requested_section)),
            ("counterpart", resp.counterpart_results, resp.counterpart_act or "?",
             str(resp.counterpart_section or "")),
        ):
            if name == "counterpart" and not resp.counterpart_act:
                continue
            st = panel_stats(hits, str(exp_act).upper(), exp_sec)
            bucket = sides[name]
            bucket["n"] += 1
            for key in ("nonempty", "top1_act_ok", "top1_sec_ok", "act_pure", "sec_exact"):
                bucket[key] += 1 if st[key] else 0
            if not (st["top1_act_ok"] and st["top1_sec_ok"]):
                failures.append(
                    f"  {act} {sec} -> {name} [{resp.counterpart_act} {resp.counterpart_section}] "
                    f"top1={st['acts'][:1]}/{st['secs'][:1]} "
                    f"panel acts={st['acts']} secs={st['secs']}"
                )

    def rate(bucket, key):
        n = bucket["n"]
        return f"{bucket[key]}/{n} = {bucket[key] / n:.4f}" if n else "n/a"

    print("\n=== requested panel (the act/section the user typed) ===", flush=True)
    for key in ("nonempty", "top1_act_ok", "top1_sec_ok", "act_pure", "sec_exact"):
        print(f"  {key:<12} {rate(sides['requested'], key)}", flush=True)
    print("=== counterpart panel (mapped act/section) ===", flush=True)
    for key in ("nonempty", "top1_act_ok", "top1_sec_ok", "act_pure", "sec_exact"):
        print(f"  {key:<12} {rate(sides['counterpart'], key)}", flush=True)

    if latencies:
        lat = sorted(latencies)
        print(f"\nlatency/compare: p50={statistics.median(lat):.0f}ms "
              f"p95={lat[max(0, int(len(lat) * 0.95) - 1)]:.0f}ms max={lat[-1]:.0f}ms "
              f"(n={len(lat)})", flush=True)

    if search_calls:
        walls = sorted(c["wall_ms"] for c in search_calls)
        print(f"\nper-retrieval wall: p50={statistics.median(walls):.0f}ms "
              f"p95={walls[max(0, int(len(walls) * 0.95) - 1)]:.0f}ms "
              f"max={walls[-1]:.0f}ms (n={len(walls)})", flush=True)
        by_via = {}
        for call in search_calls:
            by_via.setdefault(call["via"], []).append(call["wall_ms"])
        for via in sorted(by_via):
            vals = sorted(by_via[via])
            print(f"  {via:<9} n={len(vals)} p50={statistics.median(vals):.0f}ms "
                  f"max={vals[-1]:.0f}ms", flush=True)
        stages = {}
        for call in search_calls:
            for name, ms in call["timings"].items():
                stages.setdefault(name, []).append(float(ms))
        if stages:
            print("stage p50/p95 (ms):", flush=True)
            for name in sorted(stages):
                vals = sorted(stages[name])
                p50 = statistics.median(vals)
                p95 = vals[max(0, int(len(vals) * 0.95) - 1)]
                print(f"  {name:<14} p50={p50:>9.1f}  p95={p95:>9.1f}  n={len(vals)}",
                      flush=True)
        else:
            print("  (filtered pipeline: no stage info - see via=wall times)",
                  flush=True)
    if mapping_misses:
        print(f"\nmapping misses ({len(mapping_misses)}):", flush=True)
        for row in mapping_misses:
            print(f"  {row}", flush=True)
    if failures:
        print(f"\npanel failures ({len(failures)}):", flush=True)
        for row in failures:
            print(row, flush=True)
    else:
        print("\nall panels: top-1 act+section correct", flush=True)


if __name__ == "__main__":
    main()
