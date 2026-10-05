"""Dump the metadata keys carried by one pushed vector, and confirm the two
fields the eval's section_hit() depends on (real_act_name / act_name) and the
'act' field the API's _infer_act() uses are all present."""

import os
from pathlib import Path

from pinecone import Pinecone

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


pc = Pinecone(api_key=env("PINECONE_API_KEY"))
ix = pc.Index(os.getenv("HECTOR_EVAL_INDEX", "hector"))

for vid in ("ipc-1860:s:302:0", "bns-2023:s:103:0"):
    res = ix.fetch(ids=[vid])
    vecs = getattr(res, "vectors", None) or res.get("vectors") or {}
    v = vecs.get(vid)
    md = (v.metadata if hasattr(v, "metadata") else None) or {}
    print(f"\n{vid}: {len(md)} metadata keys")
    for k in sorted(md):
        val = str(md[k])
        print(f"   {k} = {val[:70]!r}")
    for need in ("act", "act_name", "real_act_name", "section_number",
                 "section_title", "source"):
        print(f"   CHECK {need}: {'PRESENT' if need in md else '*** MISSING ***'}")
