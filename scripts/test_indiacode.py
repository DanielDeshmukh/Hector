"""Test India Code API for downloadable PDF links."""
import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json,text/html,*/*",
}

# India Code website search - find act pages with PDF links
base = "https://www.indiacode.nic.in"
search_page = base + "/handle/123456789/2289"

# Try to get the main page and find act listing
try:
    req = urllib.request.Request(base, headers=headers)
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    html = resp.read().decode("utf-8", errors="replace")
    # Find PDF links
    pdf_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', html, re.IGNORECASE)
    print(f"Found {len(pdf_links)} PDF links on main page")
    for link in pdf_links[:10]:
        print(f"  {link}")
except Exception as e:
    print(f"Main page: {str(e)[:80]}")

# Try handle pages for specific acts
act_handles = [
    ("Hindu Marriage", "/handle/123456789/2088"),
    ("Indian Contract", "/handle/123456789/1996"),
    ("CPC", "/handle/123456789/1932"),
    ("Companies 2013", "/handle/123456789/17468"),
    ("Competition", "/handle/123456789/17000"),
    ("RTI", "/handle/123456789/20054"),
]

for name, path in act_handles:
    try:
        url = base + path
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode("utf-8", errors="replace")
        # Find bitstream/PDF links
        pdf_links = re.findall(r'href="(/bitstream/[^"]*\.pdf[^"]*)"', html, re.IGNORECASE)
        if pdf_links:
            print(f"OK   {name}: {len(pdf_links)} PDF links")
            for link in pdf_links[:3]:
                print(f"       {base}{link}")
        else:
            # Try finding any bitstream links
            bit_links = re.findall(r'href="(/bitstream/[^"]*)"', html)
            if bit_links:
                print(f"OK   {name}: {len(bit_links)} bitstream links (checking for PDFs...)")
                for link in bit_links[:3]:
                    full = base + link
                    print(f"       {full}")
            else:
                print(f"MISS {name}: no links found")
    except Exception as e:
        print(f"ERR  {name}: {str(e)[:60]}")
