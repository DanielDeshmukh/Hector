"""Compare the two surviving NIM chat models on the actual RAG generation
prompt shape, so LIVE_MODEL is chosen on grounding-relevant output quality
(not just latency). Prints ids/timings/snippets only, never the key.

Console-safe: all output is passed through errors='replace' because the
Windows codepage chokes on some model unicode (that was a probe-script bug,
not a model failure)."""

import os
import sys
import time
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
]

SYSTEM = (
    "You are a legal assistant. Answer ONLY from the supplied context. "
    "Cite the section number for every claim. If the context does not "
    "support an answer, say so. Do not add preambles."
)
CONTEXT = (
    "Section 302. Punishment for murder.\n"
    "Whoever commits murder shall be punished with death or imprisonment "
    "for life, and shall also be liable to fine.\n"
    "Section 303. Punishment for murder by life-convict.\n"
    "Whoever, being under sentence of imprisonment for life, commits murder, "
    "shall be punished with death."
)
QUESTION = "What punishment does the Indian Penal Code prescribe for murder?"

with httpx.Client(timeout=90) as c:
    for m in CANDIDATES:
        t0 = time.time()
        try:
            r = c.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json={
                    "model": m,
                    "messages": [{"role": "system", "content": SYSTEM},
                                 {"role": "user",
                                  "content": f"Context:\n{CONTEXT}\n\n"
                                             f"Question: {QUESTION}"}],
                    "max_tokens": 300,
                    "temperature": 0.0,
                },
            )
            dt = (time.time() - t0) * 1000
            if r.status_code == 200:
                data = r.json()
                txt = (data["choices"][0]["message"].get("content") or "")
                u = data.get("usage") or {}
                print(f"OK   {dt:7.0f}ms in={u.get('prompt_tokens')} "
                      f"out={u.get('completion_tokens')} {m}")
                print(f"       {txt.strip()[:420]!r}")
            else:
                print(f"FAIL {dt:7.0f}ms HTTP {r.status_code} {m} -> "
                      f"{r.text.replace(chr(10), ' ')[:140]}")
        except Exception as exc:
            print(f"ERR  {m}: {type(exc).__name__}: {exc}")
        print("-" * 70, flush=True)
