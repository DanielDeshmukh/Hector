"""diag_unattached.py - read-only: where do the unattached footnotes' refs sit?

For each unattached footnote: span bounds, heading label, whether a ref with
the same number exists inside span / on the marker line / on the next marker
line / anywhere on the same page / document-wide. No writes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v2_common as V
import v2_scanner as S

ACT = "ipc-1860"


def main():
    V.tee(f"{ACT}_diag_unattached")
    doc = V.fitz.open(str(V.SOURCES / f"{ACT}.pdf"))
    sc = S.scan_document(doc, start_page=V.body_scan_start(ACT))
    doc.close()
    lines = sc["lines"]
    un = [f for f in sc["footnotes"] if f["status"] == "unattached"]

    seen = set()
    refs = []
    for ln in lines:
        if ln["label"] is not None:
            continue
        for rx in S.INLINE_REF_RES:
            for m in rx.finditer(ln["text"]):
                k = (ln["i"], int(m.group(1)))
                if k in seen:
                    continue
                seen.add(k)
                refs.append((ln["i"], int(m.group(1)), m.start(), ln["page"]))

    by_num = {}
    for t in refs:
        by_num.setdefault(t[1], []).append(t)

    print(f"INLINE_REF_RES patterns: {[r.pattern for r in S.INLINE_REF_RES]}")
    print(f"unattached: {len(un)}\n")

    glued = S.INLINE_REF_RES[3]
    print("--- pattern4 (glued marker) matches across body ---")
    seen4 = set()
    for ln in lines:
        if ln["label"] is not None:
            continue
        for m in glued.finditer(ln["text"]):
            key = (ln["i"], int(m.group(1)))
            if key in seen4:
                continue
            seen4.add(key)
            print(f"  line {ln['i']} page {ln['page'] + 1} "
                  f"num={m.group(1)} ctx="
                  f"{ln['text'][max(0, m.start() - 15):m.end() + 30]!r}")
    print(f"pattern4 total: {len(seen4)}\n")

    def lbl(i):
        if i < 0 or i >= len(lines):
            return "OOR"
        return str(lines[i].get("label"))

    for f in un:
        n = int(f["num"])
        lo, hi = f["span"]
        in_span = [t for t in refs if lo < t[0] < hi and t[1] == n]
        at_lo = [t for t in refs if t[0] == lo and t[1] == n]
        at_hi = [t for t in refs if t[0] == hi and t[1] == n]
        page = lines[f["members"][0]]["page"]
        on_page = [t for t in by_num.get(n, []) if t[3] == page]
        head = lines[lo]["text"][:70] if 0 <= lo < len(lines) else "?"
        print(
            f"fn p{f['pdf_page']} n={n} span=({lo},{hi}) "
            f"head_lbl={lbl(lo)} next_lbl={lbl(hi)} | "
            f"in_span={len(in_span)} at_marker={len(at_lo)} "
            f"at_next={len(at_hi)} same_page={len(on_page)} "
            f"docwide={len(by_num.get(n, []))}"
        )
        print(f"   head: {head}")
        if not in_span and not at_lo:
            for t in on_page[:3]:
                print(f"   same-page ref line {t[0]}: "
                      f"{lines[t[0]]['text'][max(0, t[2] - 30):t[2] + 40]!r}")

    print("\nCHECKPOINT diag_unattached done")


if __name__ == "__main__":
    main()
