"""Round 2 of the NIM chat-model probe: find a fast, preamble-free candidate
to pair with nvidia/nemotron-3-ultra-550b-a55b (verified OK in round 1).

Prints model ids and timings only, never the key."""

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
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nemotron-nano-3-30b-a3b",
    "nvidia/nemotron-4-340b-instruct",
    "nv-mistralai/mistral-nemo-12b-instruct",
    "google/gemma-3-12b-it",
    "nvidia/llama3-chatqa-1.5-70b",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
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
                print(f"       -> {txt.strip()[:170]!r}")
            else:
                body = r.text.replace("\n", " ")[:170]
                print(f"FAIL {dt:7.0f}ms HTTP {r.status_code} {m}")
                print(f"       -> {body}")
        except Exception as exc:
            dt = (time.time() - t0) * 1000
            print(f"ERR  {dt:7.0f}ms {m}: {type(exc).__name__}: {exc}")
