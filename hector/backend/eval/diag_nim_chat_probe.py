"""Probe candidate NIM chat models for the eval's LIVE_MODEL replacement.

The previous LIVE_MODEL (nvidia/nemotron-3-super-120b-a12b) was retired
2026-10-03T09:00Z. This sends one tiny completion to each candidate and
reports status / latency / whether the reply looks sane, so the replacement
is chosen on evidence rather than guesswork. Prints model ids and timings
only, never the key."""

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
    "nvidia/nemotron-3-super-120b-a12b",   # known-dead control
    "meta/llama-3.1-8b-instruct",          # nim_llm default
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/llama-3.1-nemotron-51b-instruct",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "mistralai/mistral-large-2-instruct",
]

PROMPT = ("Answer in one sentence: what does section 302 of the Indian "
          "Penal Code punish?")

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
                      "max_tokens": 80, "temperature": 0.0},
            )
            dt = (time.time() - t0) * 1000
            if r.status_code == 200:
                data = r.json()
                txt = data["choices"][0]["message"].get("content") or ""
                used = (data.get("usage") or {}).get("total_tokens")
                print(f"OK   {dt:7.0f}ms tok={used!s:>5} {m}")
                print(f"       -> {txt.strip()[:150]!r}")
            else:
                body = r.text.replace("\n", " ")[:180]
                print(f"FAIL {dt:7.0f}ms HTTP {r.status_code} {m}")
                print(f"       -> {body}")
        except Exception as exc:
            dt = (time.time() - t0) * 1000
            print(f"ERR  {dt:7.0f}ms {m}: {type(exc).__name__}: {exc}")
