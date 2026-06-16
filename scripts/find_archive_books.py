"""Search archive.org for Indian legal bare acts with downloadable PDFs."""

import urllib.request
import urllib.parse
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

searches = [
    "hindu marriage act 1955 bare act",
    "indian contract act 1872 bare act",
    "code of civil procedure 1908 bare act",
    "companies act 2013 bare act",
    "competition act 2002 bare act",
    "right to information act 2005",
    "environment protection act 1986",
    "indian forest act 1927",
    "copyright act 1957 bare act",
    "patents act 1970 bare act",
    "indian partnership act 1932",
    "sale of goods act 1930",
    "indian easements act 1882",
    "indian trusts act 1882",
    "indian stamp act 1899",
    "contempt of courts act 1971",
    "industrial disputes act 1947",
    "factories act 1948 bare act",
    "motor vehicles act 1988 bare act",
    "negotiable instruments act 1881 bare act",
    "transfer of property act 1882 bare act",
    "special marriage act 1954",
    "hindu succession act 1956",
    "dowry prohibition act 1961",
    "water prevention control pollution act 1974",
    "air prevention control pollution act 1981",
    "foreign exchange management act 1999",
    "sebi act 1992 bare act",
]

results = []
for q in searches:
    try:
        encoded = urllib.parse.quote(q)
        api_url = (
            f"https://archive.org/advancedsearch.php?"
            f"q={encoded}&fl[]=identifier&fl[]=title&fl[]=format"
            f"&rows=5&output=json"
        )
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        data = json.loads(resp.read())
        docs = data.get("response", {}).get("docs", [])
        for doc in docs:
            fmts = doc.get("format", [])
            has_pdf = any("PDF" in f.upper() for f in fmts)
            if has_pdf:
                ident = doc["identifier"]
                title = doc.get("title", "Unknown")
                dl_url = f"https://archive.org/download/{ident}/{ident}.pdf"
                results.append((q, title, ident, dl_url))
                print(f"FOUND  {q[:35]:<35} -> {ident[:50]}")
                break
        else:
            print(f"MISS   {q[:35]}")
    except Exception as e:
        print(f"ERR    {q[:35]}: {str(e)[:60]}")

print(f"\nFound {len(results)} books with PDFs")
for q, title, ident, url in results:
    print(f"  {title[:60]}")
    print(f"    {url}")
