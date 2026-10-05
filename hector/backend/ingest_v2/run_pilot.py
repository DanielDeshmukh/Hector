#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""run_pilot.py - run the ingest_v2 pilot end-to-end for one act:
steps 2 -> 7 in order, stopping at the first non-zero exit.

Usage: python run_pilot.py --act <act_id>
Writes: results/<act_id>_timing.json (updated after every step).
Each child also tees its own results/<act_id>_<step>.log.
"""

import argparse
import json
import subprocess
import sys
import time

import v2_common as V

STEPS = [
    (2, "step2_inspect"),
    (3, "step3_clean"),
    (4, "step4_segment"),
    (5, "step5_records"),
    (6, "step6_validate"),
    (7, "step7_report"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_run_pilot")
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2

    timing_path = V.RESULTS / f"{act_id}_timing.json"
    timing = {"act_id": act_id, "steps": {}}
    print("=" * 76, flush=True)
    print(f"RUN PILOT {act_id} ({act['act_name']}) - steps "
          f"{', '.join(str(n) for n, _ in STEPS)}", flush=True)
    print("=" * 76, flush=True)

    rc = 0
    for num, name in STEPS:
        script = V.INGEST / f"{name}.py"
        if not script.exists():
            print(f"FATAL: {script} missing", flush=True)
            rc = 2
            break
        print(f"\n--- step {num}: {name} "
              f"{'-' * max(1, 60 - len(name))}", flush=True)
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, "-u", str(script), "--act", act_id],
            cwd=str(V.ROOT / "hector" / "backend"),
        )
        dt = round(time.time() - t0, 2)
        timing["steps"][name] = {"exit": proc.returncode, "seconds": dt}
        V.write_json(timing_path, timing)
        print(f"--- step {num}: {name} exit={proc.returncode} "
              f"({dt}s) ---", flush=True)
        if proc.returncode != 0:
            rc = proc.returncode
            for n2, name2 in STEPS[num - 1:]:
                if name2 not in timing["steps"]:
                    timing["steps"][name2] = {"exit": "skipped",
                                              "seconds": 0}
            V.write_json(timing_path, timing)
            print(f"\nSTOPPED at step {num} ({name}) with exit "
                  f"{proc.returncode}; remaining steps skipped.", flush=True)
            break
    else:
        print(f"\nALL STEPS OK for {act_id}", flush=True)

    print(f"\n[write] results/{act_id}_timing.json", flush=True)
    print(f"[exit] {rc}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
