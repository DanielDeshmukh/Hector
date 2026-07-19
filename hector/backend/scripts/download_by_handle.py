"""Download Indian bare acts using known India Code handle IDs."""

import urllib.request
import ssl
import os
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/pdf,*/*",
}

BOOKS_DIR = r"D:\Vs Code\VS code\Hector\data\Books"

# India Code handle IDs for known acts
# Format: (handle_id, filename, description)
INDIA_CODE_BOOKS = [
    ("2088", "Hindu_Marriage_Act_1955.pdf", "Hindu Marriage Act"),
    ("2093", "Hindu_Succession_Act_1956.pdf", "Hindu Succession Act"),
    (
        "2094",
        "Hindu_Minority_And_Guardianship_Act_1956.pdf",
        "Hindu Minority & Guardianship",
    ),
    ("2074", "Special_Marriage_Act_1954.pdf", "Special Marriage Act"),
    ("1963", "Dowry_Prohibition_Act_1961.pdf", "Dowry Prohibition Act"),
    ("2001", "Industrial_Disputes_Act_1947.pdf", "Industrial Disputes Act"),
    ("2015", "Factories_Act_1948.pdf", "Factories Act"),
    ("1954", "Indian_Partnership_Act_1932.pdf", "Indian Partnership Act"),
    ("1949", "Sale_of_Goods_Act_1930.pdf", "Sale of Goods Act"),
    ("1932", "Code_Of_Civil_Procedure_1908.pdf", "Code of Civil Procedure"),
    ("1643", "Code_Of_Civil_Procedure_1908_v2.pdf", "CPC v2"),
    ("1996", "Indian_Contract_Act_1872_v2.pdf", "Indian Contract Act"),
    ("1654", "Easements_Act_1882.pdf", "Indian Easements Act"),
    ("1651", "Trusts_Act_1882.pdf", "Indian Trusts Act"),
    ("1762", "Stamp_Act_1899.pdf", "Indian Stamp Act"),
    ("1990", "Environment_Protection_Act_1986.pdf", "Environment Protection Act"),
    ("1695", "Forest_Act_1927.pdf", "Indian Forest Act"),
    ("2056", "Copyright_Act_1957.pdf", "Copyright Act"),
    ("1971", "Patents_Act_1970.pdf", "Patents Act"),
    ("17468", "Companies_Act_2013.pdf", "Companies Act 2013"),
    ("17000", "Competition_Act_2002.pdf", "Competition Act"),
    ("20054", "Right_To_Information_Act_2005.pdf", "RTI Act"),
]

downloaded = 0
failed = 0

for handle, filename, desc in INDIA_CODE_BOOKS:
    dest = os.path.join(BOOKS_DIR, filename)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"SKIP {filename} (exists)")
        continue

    # Try fetching the handle page first to find actual PDF link
    page_url = f"https://www.indiacode.nic.in/handle/123456789/{handle}"
    pdf_url = None

    try:
        req = urllib.request.Request(
            page_url,
            headers={
                "User-Agent": headers["User-Agent"],
                "Accept": "text/html,*/*",
            },
        )
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode("utf-8", errors="replace")

        import re

        # Find bitstream PDF links
        bit_links = re.findall(
            r'href="(/bitstream/123456789/' + handle + r'/[^"]*\.pdf[^"]*)"',
            html,
            re.IGNORECASE,
        )
        if bit_links:
            pdf_url = "https://www.indiacode.nic.in" + bit_links[0]
        else:
            # Try generic bitstream
            bit_links = re.findall(
                r'href="(/bitstream/[^"]*\.pdf[^"]*)"', html, re.IGNORECASE
            )
            if bit_links:
                pdf_url = "https://www.indiacode.nic.in" + bit_links[0]
    except Exception:
        pass

    if not pdf_url:
        # Fallback: try common bitstream patterns
        for pattern in [
            f"https://www.indiacode.nic.in/bitstream/123456789/{handle}/1/act.pdf",
            f"https://www.indiacode.nic.in/bitstream/123456789/{handle}/A0-{handle}.pdf",
        ]:
            try:
                req = urllib.request.Request(pattern, headers=headers)
                resp = urllib.request.urlopen(req, timeout=10, context=ctx)
                data = resp.read(20)
                if data[:5] == b"%PDF-":
                    pdf_url = pattern
                    break
            except Exception:
                continue

    if not pdf_url:
        print(f"MISS {filename}: no PDF URL found for handle {handle}")
        failed += 1
        continue

    # Download the PDF
    try:
        req = urllib.request.Request(pdf_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=60, context=ctx)
        data = resp.read()

        if len(data) < 500 or not data[:5] == b"%PDF-":
            print(f"SKIP {filename}: not a valid PDF ({len(data)} bytes)")
            failed += 1
            continue

        with open(dest, "wb") as f:
            f.write(data)

        size_kb = len(data) / 1024
        print(f"OK   {filename}: {size_kb:.0f} KB from {pdf_url[:60]}...")
        downloaded += 1

    except Exception as e:
        print(f"ERR  {filename}: {str(e)[:60]}")
        failed += 1

    time.sleep(1.5)

print(f"\nDone: {downloaded} downloaded, {failed} failed")
total = len([f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf")])
print(f"Total PDFs in Books: {total}")
