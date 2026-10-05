"""Probe the query_intelligence model and confirm the fallback chain models
before editing nim_llm.py defaults. Prints ids/timings only, never the key."""

import os
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]


def env(name):
    for line in (ROOT / ".env").read_text(encoding="utf-8",
                                           errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, v = s.partition("=")
            if k.strip() == name:
                return v.strip().strip('"').strip("'")
    return os.environ.get(name, "")


base = env("NIM_BASE_URL") or "https://integrate.api.nvidia.com/v1"
key = env("NIM_API_KEY")

CANDIDATES = [
    "nvidia/llama-3.1-nemotron-nano-8b-v1",       # nim_llm query_intelligence
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nemotron-3-ultra-550b-a55b",
]

PROMPT = "Classify the intent of: 'what does section 302 say?'"

with httpx.Client(timeout=60) as c:
    for m in CANDIDATES:
        t0 = time.time()
        try:
            r = c.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json={"model": m, "messages": [{"role": "user",
                                                "content": PROMPT}],
                      "max_tokens": 60, "temperature": 0.0},
            )
            dt = (time.time() - t0) * 1000
            if r.status_code == 200:
                txt = (r.json()["choices"][0]["message"].get("content") or "")
                print(f"OK   {dt:7.0f}ms {m}\n       -> {txt.strip()[:150]!r}")
            else:
                print(f"FAIL {dt:7.0f}ms HTTP {r.status_code} {m} "
                      f"-> {r.text.replace(chr(10), ' ')[:140]}")
        except Exception as exc:
            print(f"ERR  {m}: {type(exc).__name__}: {exc}")
