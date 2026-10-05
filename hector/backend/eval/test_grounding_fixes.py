"""Guard the three grounding fixes before spending a 60-question run on them:

1. verifier: "(not in sources)" and "... but not Section N" now classify as
   negated (Round 6 markers), and ordinary legal prose does NOT.
2. run_gold_eval: the gate denominator is n_assertive, not n_mentions, with
   the 0.99 threshold untouched.

Fails loudly (exit 1) on any regression."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[3]
# run_gold_eval.py puts hector\api on sys.path and imports core.verifier,
# so mirror that exactly (the package root is hector\api, not the repo root).
sys.path.insert(0, str(ROOT / "hector" / "api"))

from core.verifier import grounding_report  # noqa: E402

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}: got={got} want={want}")
    if not ok:
        FAILURES.append(label)


print("negation detection (verifier.grounding_report):")

r = grounding_report(
    "- **Section 125** (not in sources): Waging war against any Asiatic Power.",
    "Section 127 Whoever receives any property ... sections 125 and 126.",
)
m = [x for x in r["mentions"] if x["section"] == "125"][0]
check("'(not in sources)' is negated", m["negated"], True)

r = grounding_report(
    "The retrieved sources cover Sections 225B, 216, 201 of the IPC, "
    "and Section 231 of the BNS, but not Section 275.",
    "Section 231 BNS Whoever ...",
)
m = [x for x in r["mentions"] if x["section"] == "275"][0]
check("'but not Section 275' is negated", m["negated"], True)

r = grounding_report(
    "Section 127 punishes receiving property taken by war, "
    "with imprisonment up to seven years and a fine.",
    "Section 127 Whoever receives any property knowing the same to have "
    "been taken in the commission of any of the offences mentioned in "
    "sections 125 and 126 shall be punished with imprisonment ... seven years.",
)
check("plain legal claim is NOT negated",
      any(not x["negated"] for x in r["mentions"]), True)
check("plain legal claim IS grounded",
      r["n_grounded"] > 0, True)

r = grounding_report(
    "The Act, 2019 does not contain a section 502, but not section 503.",
    "Section 503.",
)
check("marker gated on source context (no source words => assertive)",
      all(not x["negated"] for x in r["mentions"]), True)

print("\ngate denominator (run_gold_eval):")
lines = (Path(__file__).resolve().parent / "run_gold_eval.py").read_text(
    encoding="utf-8").splitlines()
denom = [l.strip() for l in lines if "n_ment = gnd.get(" in l]
check("exactly one denominator assignment", len(denom), 1)
check("denominator uses n_assertive",
      bool(denom) and '"n_assertive"' in denom[0], True)
check("n_mentions no longer read for the gate",
      any("gnd.get(\"n_mentions\")" in l for l in lines), False)
# The three gate thresholds (0.98 / 0.99 / 0.991) are deliberately NOT in
# this codebase - the eval emits raw numbers with CIs and the gates are
# judged against the documented values. Asserting that stays true is the
# real anti-regression guard: nothing here can quietly loosen a threshold.
src = "\n".join(lines)
check("no numeric gate thresholds introduced into run_gold_eval",
      "0.99" not in src.replace("threshold unchanged at 0.99", "")
      .replace("at 0.99)", "").replace(">=0.99", ""), True)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print("all checks passed")
