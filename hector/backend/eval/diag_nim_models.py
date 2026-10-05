"""List currently available NIM chat model ids so LIVE_MODEL can be replaced
with something that is not EOL. Prints model ids only, never the key."""

import os
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
print(f"NIM_BASE_URL={base}")
print(f"NIM_API_KEY present={bool(key)}")

with httpx.Client(timeout=30) as c:
    r = c.get(f"{base}/models",
              headers={"Authorization": f"Bearer {key}"})
    print(f"GET /models -> {r.status_code}")
    r.raise_for_status()
    ids = [m.get("id") for m in r.json().get("data", [])]

print(f"total models listed: {len(ids)}")

# Focus on instruct/chat models a RAG generator could actually use.
watch = ("nemotron", "llama", "mistral", "qwen", "gemma", "phi")
chat = sorted(i for i in ids if i and any(w in i.lower() for w in watch))
print(f"\nchat-capable candidates ({len(chat)}):")
for i in chat:
    print(f"   {i}")

dead = [i for i in ids if "nemotron-3-super-120b-a12b" in (i or "")]
print(f"\nEOL model still listed: {dead or 'no (it is gone from the catalog)'}")
