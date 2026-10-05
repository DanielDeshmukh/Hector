import collections
import json

d = json.load(open(r"D:\Vs Code\VS code\Hector\hector\backend\ingest_v2\results\books_triage.json", encoding="utf-8"))
books = d["books"] if isinstance(d, dict) and "books" in d else d
if isinstance(books, dict):
    books = [dict(v, file=k) for k, v in books.items()]

print(collections.Counter(b.get("verdict") or b.get("status") for b in books))
print()
for b in books:
    v = b.get("verdict") or b.get("status")
    if v == "PARSEABLE":
        continue
    f = str(b.get("file"))
    f = f[:44] if len(f) > 44 else f
    print("%-14s %-46s markers=%-5s span=%-10s dens=%-6s start=%s" % (
        v, f, b.get("markers"), b.get("span"), b.get("density"), b.get("start_page")))
