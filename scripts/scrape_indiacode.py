"""Scrape India Code website for actual bare act PDF links."""
import urllib.request
import urllib.parse
import ssl
import json
import re
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Acts to search for on India Code
acts = [
    ("Hindu Marriage Act 1955", "Hindu_Marriage_Act_1955.pdf"),
    ("Hindu Succession Act 1956", "Hindu_Succession_Act_1956.pdf"),
    ("Indian Partnership Act 1932", "Indian_Partnership_Act_1932.pdf"),
    ("Sale of Goods Act 1930", "Sale_of_Goods_Act_1930.pdf"),
    ("Indian Contract Act 1872", "Indian_Contract_Act_1872_v2.pdf"),
    ("Code of Civil Procedure 1908", "Code_Of_Civil_Procedure_1908.pdf"),
    ("Companies Act 2013", "Companies_Act_2013.pdf"),
    ("Competition Act 2002", "Competition_Act_2002.pdf"),
    ("Right to Information Act 2005", "Right_To_Information_Act_2005.pdf"),
    ("Industrial Disputes Act 1947", "Industrial_Disputes_Act_1947.pdf"),
    ("Factories Act 1948", "Factories_Act_1948.pdf"),
    ("Environment Protection Act 1986", "Environment_Protection_Act_1986.pdf"),
    ("Indian Forest Act 1927", "Forest_Act_1927.pdf"),
    ("Copyright Act 1957", "Copyright_Act_1957.pdf"),
    ("Patents Act 1970", "Patents_Act_1970.pdf"),
    ("Trade Marks Act 1999", "Trade_Marks_Act_1999.pdf"),
    ("Special Marriage Act 1954", "Special_Marriage_Act_1954.pdf"),
    ("Dowry Prohibition Act 1961", "Dowry_Prohibition_Act_1961.pdf"),
    ("Indian Easements Act 1882", "Easements_Act_1882.pdf"),
    ("Indian Trusts Act 1882", "Trusts_Act_1882.pdf"),
    ("Indian Stamp Act 1899", "Stamp_Act_1899.pdf"),
    ("Contempt of Courts Act 1971", "Contempt_Of_Courts_Act_1971.pdf"),
    ("Water Act 1974", "Water_Act_1974.pdf"),
    ("Air Act 1981", "Air_Act_1981.pdf"),
    ("FEMA 1999", "FEMA_1999.pdf"),
    ("SEBI Act 1992", "SEBI_Act_1992.pdf"),
    ("Negotiable Instruments Act 1881", "Negotiable_Instruments_Act_1881.pdf"),
    ("Motor Vehicles Act 1988", "Motor_Vehicles_Act_1988_v2.pdf"),
    ("Transfer of Property Act 1882", "Transfer_of_Property_Act_1882_v2.pdf"),
    ("Insolvency and Bankruptcy Code 2016", "IBC_2016.pdf"),
]

books_dir = r"D:\Vs Code\VS code\Hector\data\Books"
downloaded = 0
failed = 0

for act_name, filename in acts:
    dest = f"{books_dir}\\{filename}"
    import os
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"SKIP {filename} (exists)")
        continue

    # Search India Code
    try:
        search_url = (
            "https://www.indiacode.nic.in/handle/123456789/2289/simple-search"
            "?searchText=" + urllib.parse.quote(act_name)
            + "&rpp=10&sort_by=score&order=desc&rtype=simple"
        )
        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode("utf-8", errors="replace")

        # Find handle links
        handles = re.findall(r'href="(/handle/123456789/\d+)"', html)
        if not handles:
            print(f"MISS {filename}: no handles found for '{act_name}'")
            failed += 1
            continue

        # Try first handle
        handle = handles[0]
        detail_url = "https://www.indiacode.nic.in" + handle
        req2 = urllib.request.Request(detail_url, headers=headers)
        resp2 = urllib.request.urlopen(req2, timeout=15, context=ctx)
        html2 = resp2.read().decode("utf-8", errors="replace")

        # Find bitstream PDF links
        bit_links = re.findall(
            r'href="(/bitstream/123456789/\d+/[^"]*\.pdf[^"]*)"',
            html2, re.IGNORECASE
        )

        if not bit_links:
            print(f"MISS {filename}: no PDF bitstreams for '{act_name}'")
            failed += 1
            continue

        # Download first PDF
        pdf_url = "https://www.indiacode.nic.in" + bit_links[0]
        req3 = urllib.request.Request(pdf_url, headers={
            "User-Agent": headers["User-Agent"],
            "Accept": "application/pdf,*/*",
        })
        resp3 = urllib.request.urlopen(req3, timeout=60, context=ctx)
        data = resp3.read()

        if len(data) < 500 or not data[:5] == b"%PDF-":
            print(f"SKIP {filename}: not a valid PDF ({len(data)} bytes)")
            failed += 1
            continue

        with open(dest, "wb") as f:
            f.write(data)

        size_kb = len(data) / 1024
        print(f"OK   {filename}: {size_kb:.0f} KB")
        downloaded += 1

    except Exception as e:
        print(f"ERR  {filename}: {str(e)[:60]}")
        failed += 1

    time.sleep(1.5)

print(f"\nDone: {downloaded} downloaded, {failed} failed")
