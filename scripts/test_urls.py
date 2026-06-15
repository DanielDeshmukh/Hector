import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()
session.headers.update(headers)
session.verify = False

# Strategy: Search on indiacode.nic.in to find correct handle IDs
# Then get bitstream links from those handles

# Known working handles from our tests
known_handles = {
    "IPC_old": "123456789/2088",  # This gives A2007-23.pdf which is an amendment, NOT the IPC
    "CrPC_old": "123456789/1526", # This gives A1963__19.pdf
}

# Let's search for the actual acts
print("=== Searching indiacode.nic.in for correct handle IDs ===")
search_url = "https://www.indiacode.nic.in/search"
acts_to_search = [
    ("Indian Penal Code 1860", "IPC"),
    ("Bharatiya Nyaya Sanhita 2023", "BNS"),
    ("Code of Criminal Procedure 1973", "CrPC"),
    ("Bharatiya Nagarik Suraksha Sanhita 2023", "BNSS"),
    ("Indian Evidence Act 1872", "IEA"),
    ("Bharatiya Sakshya Adhiniyam 2023", "BSA"),
    ("Constitution of India", "Constitution"),
]

for search_term, short_name in acts_to_search:
    try:
        r = session.get(search_url, params={"search_field": "All", "search_text": search_term}, timeout=15, allow_redirects=True)
        # Find handle links
        handles = re.findall(r'/handle/(\d+/\d+)', r.text)
        unique_handles = list(set(handles))
        print(f"\n{short_name}: {r.status_code}, handles found: {unique_handles[:3]}")
        
        if unique_handles:
            # Try the first handle
            handle = unique_handles[0]
            handle_url = f"https://www.indiacode.nic.in/handle/{handle}"
            r2 = session.get(handle_url, timeout=15)
            bitstreams = re.findall(r'/bitstream/[^"\'>\s]+\.pdf', r2.text)
            print(f"  Handle {handle}: {r2.status_code}, bitstreams: {list(set(bitstreams))[:3]}")
    except Exception as e:
        print(f"{short_name}: Error - {e}")

# Also try the simple approach: just browse the act listing pages
print("\n\n=== Browsing act listing pages ===")
listing_urls = [
    "https://www.indiacode.nic.in/show-data?actid=AC_CEN_5_20_00040_202321_1517807320240",
    "https://www.indiacode.nic.in/show-data?actid=AC_CEN_5_20_00040_202321_1517807320240&sectionId=0",
]
for url in listing_urls:
    try:
        r = session.get(url, timeout=15)
        print(f"{r.status_code} - {url[:80]}")
        if r.status_code == 200:
            # Look for PDF links
            pdfs = re.findall(r'["\']([^"\']*\.pdf)["\']', r.text, re.IGNORECASE)
            print(f"  PDFs: {pdfs[:5]}")
            # Look for download links
            downloads = re.findall(r'href=["\']([^"\']*download[^"\']*)["\']', r.text, re.IGNORECASE)
            print(f"  Downloads: {downloads[:5]}")
    except Exception as e:
        print(f"Error: {e}")

# Try the show-data endpoint which seems to be the actual act viewer
print("\n\n=== Trying show-data endpoint ===")
# BNS 2023 act ID
show_data_urls = [
    "https://www.indiacode.nic.in/show-data?aid=3688",
    "https://www.indiacode.nic.in/show-data?aid=2088",
    "https://www.indiacode.nic.in/show-data?aid=1526",
]
for url in show_data_urls:
    try:
        r = session.get(url, timeout=15)
        print(f"\n{r.status_code} - {url}")
        # Look for PDF download or bitstream
        bitstreams = re.findall(r'bitstream[^"\'>\s]*', r.text)
        downloads = re.findall(r'download[^"\'>\s]*', r.text, re.IGNORECASE)
        print(f"  Bitstreams: {bitstreams[:3]}")
        print(f"  Downloads: {downloads[:3]}")
        # Look for iframe or embed
        embeds = re.findall(r'<(?:iframe|embed)[^>]*src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
        print(f"  Embeds: {embeds[:3]}")
    except Exception as e:
        print(f"Error: {e}")
