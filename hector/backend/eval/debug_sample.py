import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
import run_gold_eval as rge  # noqa: E402

print("import-time GOLD_SAMPLE =", rge.GOLD_SAMPLE,
      "SEED =", rge.GOLD_SAMPLE_SEED)
print("env HECTOR_EVAL_SAMPLE =", os.getenv("HECTOR_EVAL_SAMPLE"))
print("GOLD_PATH =", rge.GOLD_PATH, "exists:", Path(rge.GOLD_PATH).exists())
raw = rge.read_jsonl(rge.GOLD_PATH)
print("raw gold rows:", len(raw))

rge.GOLD_SAMPLE = 200
rge.GOLD_SAMPLE_SEED = 20261013
print("after set: GOLD_SAMPLE =", rge.GOLD_SAMPLE)
g = rge.load_gold()
print("load_gold() ->", len(g))
