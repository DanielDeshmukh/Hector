"""
HECTOR Corpus Expansion - Downloads additional Indian legal bare acts.
Sources: legislative.gov.in, indiacode.nic.in, archive.org, other gov sites.

Usage:
    python scripts/download_more_books.py              # Download all
    python scripts/download_more_books.py --dry-run    # Show what would download
    python scripts/download_more_books.py --list       # List all books
"""

import argparse
import time
import urllib.request
import urllib.error
import ssl
import json
from pathlib import Path
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "Books"
PROGRESS_FILE = BOOKS_DIR / ".download_progress.json"

# Suppress SSL for gov sites
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Book:
    filename: str
    title: str
    urls: list
    description: str = ""
    tier: int = 5


# fmt: off
ADDITIONAL_BOOKS = [
    # ── Family & Personal Law ────────────────────────────────────────
    Book(
        filename="Hindu_Marriage_Act_1955.pdf",
        title="Hindu Marriage Act, 1955",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1955-1.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2088/A1955-1.pdf",
        ],
        description="Marriage, divorce, restitution for Hindus",
        tier=2,
    ),
    Book(
        filename="Hindu_Succession_Act_1956.pdf",
        title="Hindu Succession Act, 1956",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1956-30.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2093/A1956-30.pdf",
        ],
        description="Intestate succession among Hindus",
        tier=2,
    ),
    Book(
        filename="Hindu_Minority_And_Guardianship_Act_1956.pdf",
        title="Hindu Minority and Guardianship Act, 1956",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1956-31.pdf",
        ],
        description="Guardianship of Hindu minors",
        tier=3,
    ),
    Book(
        filename="Special_Marriage_Act_1954.pdf",
        title="Special Marriage Act, 1954",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1954-43.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2074/A1954-43.pdf",
        ],
        description="Civil marriage for all citizens",
        tier=2,
    ),
    Book(
        filename="Dowry_Prohibition_Act_1961.pdf",
        title="Dowry Prohibition Act, 1961",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1961-28.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1963/A1961-28.pdf",
        ],
        description="Prohibition of dowry",
        tier=2,
    ),

    # ── Labour & Employment Law ──────────────────────────────────────
    Book(
        filename="Industrial_Disputes_Act_1947.pdf",
        title="Industrial Disputes Act, 1947",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1947-14.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2001/A1947-14.pdf",
        ],
        description="Settlement of industrial disputes",
        tier=2,
    ),
    Book(
        filename="Factories_Act_1948.pdf",
        title="Factories Act, 1948",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1948-20.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2015/A1948-20.pdf",
        ],
        description="Health, safety and welfare of factory workers",
        tier=2,
    ),
    Book(
        filename="Minimum_Wages_Act_1948.pdf",
        title="Minimum Wages Act, 1948",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1948-11.pdf",
        ],
        description="Minimum wages for scheduled employments",
        tier=3,
    ),
    Book(
        filename="Payment_of_Bonus_Act_1965.pdf",
        title="Payment of Bonus Act, 1965",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1965-21.pdf",
        ],
        description="Payment of bonus to employees",
        tier=3,
    ),
    Book(
        filename="Payment_of_Gratuities_Act_1972.pdf",
        title="Payment of Gratuity Act, 1972",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1972-36.pdf",
        ],
        description="Gratuity payment to employees",
        tier=3,
    ),
    Book(
        filename="Employees_Provident_Fund_Act_1952.pdf",
        title="Employees Provident Fund Act, 1952",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1952-19.pdf",
        ],
        description="Provident fund for employees",
        tier=3,
    ),
    Book(
        filename="Shops_And_Establishments_Act.pdf",
        title="Shops and Establishments (Model Act)",
        urls=[
            "https://labour.gov.in/sites/default/files/The%20Shops%20and%20Establishments%20Act.pdf",
        ],
        description="Regulation of conditions of work in shops",
        tier=3,
    ),

    # ── Commercial & Corporate Law ───────────────────────────────────
    Book(
        filename="Companies_Act_2013.pdf",
        title="Companies Act, 2013",
        urls=[
            "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/acts.html",
            "https://legislative.gov.in/sites/default/files/A2013-18.pdf",
        ],
        description="Regulation of companies in India",
        tier=2,
    ),
    Book(
        filename="Indian_Partnership_Act_1932.pdf",
        title="Indian Partnership Act, 1932",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1932-09.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1954/A1932-09.pdf",
        ],
        description="Law relating to partnership firms",
        tier=2,
    ),
    Book(
        filename="Sale_of_Goods_Act_1930.pdf",
        title="Sale of Goods Act, 1930",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1930-03.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1949/A1930-03.pdf",
        ],
        description="Contract relating to sale of goods",
        tier=2,
    ),
    Book(
        filename="Competition_Act_2002.pdf",
        title="Competition Act, 2002",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2002-12.pdf",
        ],
        description="Prevention of anti-competitive practices",
        tier=2,
    ),
    Book(
        filename="Securities_And_Exchange_Board_Of_India_Act_1992.pdf",
        title="SEBI Act, 1992",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1992-15.pdf",
        ],
        description="Regulation of securities market",
        tier=3,
    ),
    Book(
        filename="Foreign_Exchange_Management_Act_1999.pdf",
        title="FEMA, 1999",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1999-18.pdf",
        ],
        description="Regulation of foreign exchange",
        tier=3,
    ),
    Book(
        filename="Insolvency_And_Bankruptcy_Code_2016.pdf",
        title="Insolvency and Bankruptcy Code, 2016",
        urls=[
            "https://www.ibbi.gov.in/uploads/publication/8f4a73fe-62fa-4012-b35e-1a549c20e9f2.pdf",
        ],
        description="Insolvency resolution for companies and individuals",
        tier=2,
    ),
    Book(
        filename="Prevention_of_Money_Laundering_Act_2002.pdf",
        title="PMLA, 2002",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2002-15.pdf",
        ],
        description="Prevention of money laundering",
        tier=3,
    ),

    # ── Property & Land Law ──────────────────────────────────────────
    Book(
        filename="Real_Estate_Regulation_And_Development_Act_2016.pdf",
        title="RERA, 2016",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2016-16.pdf",
        ],
        description="Regulation of real estate sector",
        tier=2,
    ),
    Book(
        filename="Land_Acquisition_Act_2013.pdf",
        title="Right to Fair Compensation and Transparency in Land Acquisition Act, 2013",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2013-30.pdf",
        ],
        description="Land acquisition and rehabilitation",
        tier=2,
    ),
    Book(
        filename="Easements_Act_1882.pdf",
        title="Indian Easements Act, 1882",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1882-05.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1654/A1882-05.pdf",
        ],
        description="Law relating to easements and licenses",
        tier=3,
    ),

    # ── Intellectual Property ────────────────────────────────────────
    Book(
        filename="Trade_Marks_Act_1999.pdf",
        title="Trade Marks Act, 1999",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1999-47.pdf",
        ],
        description="Registration and protection of trade marks",
        tier=3,
    ),
    Book(
        filename="Copyright_Act_1957.pdf",
        title="Copyright Act, 1957",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1957-14.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2056/A1957-14.pdf",
        ],
        description="Protection of copyright",
        tier=3,
    ),
    Book(
        filename="Patents_Act_1970.pdf",
        title="Patents Act, 1970",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1970-39.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1971/A1970-39.pdf",
        ],
        description="Patent law in India",
        tier=3,
    ),

    # ── Environmental Law ────────────────────────────────────────────
    Book(
        filename="Environment_Protection_Act_1986.pdf",
        title="Environment Protection Act, 1986",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1986-29.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1990/A1986-29.pdf",
        ],
        description="Protection and improvement of environment",
        tier=3,
    ),
    Book(
        filename="Forest_Act_1927.pdf",
        title="Indian Forest Act, 1927",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1927-16.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1695/A1927-16.pdf",
        ],
        description="Protection of forests",
        tier=3,
    ),
    Book(
        filename="Water_Act_1974.pdf",
        title="Water Act, 1974",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1974-06.pdf",
        ],
        description="Prevention and control of water pollution",
        tier=3,
    ),
    Book(
        filename="Air_Act_1981.pdf",
        title="Air Act, 1981",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1981-14.pdf",
        ],
        description="Prevention and control of air pollution",
        tier=3,
    ),

    # ── Additional Procedural ────────────────────────────────────────
    Book(
        filename="Code_Of_Civil_Procedure_1908.pdf",
        title="Code of Civil Procedure, 1908",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1908-05.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1643/A1908-05.pdf",
        ],
        description="Civil procedure law",
        tier=1,
    ),
    Book(
        filename="Indian_Penal_Code_1860_Amended.pdf",
        title="IPC 1860 (Amended with BNS cross-ref)",
        urls=[
            "https://ncib.in/pdf/indian-penal-code.pdf",
        ],
        description="IPC with latest amendments",
        tier=3,
    ),
    Book(
        filename="Indian_Trusts_Act_1882.pdf",
        title="Indian Trusts Act, 1882",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1882-02.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1651/A1882-02.pdf",
        ],
        description="Law relating to trusts",
        tier=3,
    ),
    Book(
        filename="Indian_Stamps_Act_1899.pdf",
        title="Indian Stamp Act, 1899",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1899-02.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1762/A1899-02.pdf",
        ],
        description="Stamp duty law",
        tier=3,
    ),
    Book(
        filename="Contempt_Of_Courts_Act_1971.pdf",
        title="Contempt of Courts Act, 1971",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1971-70.pdf",
        ],
        description="Contempt of courts law",
        tier=3,
    ),
    Book(
        filename="Public_Premises_Eviction_Act_1971.pdf",
        title="Public Premises (Eviction) Act, 1971",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1971-42.pdf",
        ],
        description="Eviction from public premises",
        tier=3,
    ),
    Book(
        filename="Official_Languages_Act_1963.pdf",
        title="Official Languages Act, 1963",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1963-19.pdf",
        ],
        description="Official language of the Union",
        tier=3,
    ),
    Book(
        filename="Right_To_Information_Act_2005.pdf",
        title="Right to Information Act, 2005",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2005-22.pdf",
        ],
        description="Right to information for citizens",
        tier=2,
    ),
    Book(
        filename="National_Green_Tribunal_Act_2010.pdf",
        title="National Green Tribunal Act, 2010",
        urls=[
            "https://legislative.gov.in/sites/default/files/A2010-19.pdf",
        ],
        description="Establishment of National Green Tribunal",
        tier=3,
    ),
    Book(
        filename="Telegraph_Wires_Unlawful_Possession_Act_1950.pdf",
        title="Telegraph Wires Act, 1950",
        urls=[
            "https://legislative.gov.in/sites/default/files/A1950-04.pdf",
        ],
        description="Unlawful possession of telegraph wires",
        tier=3,
    ),
]
# fmt: on


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def download_book(book: Book, progress: dict, dry_run: bool = False) -> bool:
    """Download a book, trying each URL in order."""
    dest = BOOKS_DIR / book.filename

    if dest.exists() and dest.stat().st_size > 1000:
        return True  # already downloaded

    if dry_run:
        print(f"  WOULD DOWNLOAD: {book.filename}")
        for url in book.urls:
            print(f"    -> {url}")
        return False

    for url in book.urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=60, context=SSL_CTX)
            data = resp.read()

            if len(data) < 500:
                continue

            # Verify it's a PDF
            if not data[:5] == b"%PDF-":
                continue

            dest.write_bytes(data)
            progress[book.filename] = {
                "size": len(data),
                "url": url,
                "ok": True,
            }
            save_progress(progress)
            return True

        except Exception:
            continue

    progress[book.filename] = {"ok": False, "error": "all URLs failed"}
    save_progress(progress)
    return False


def main():
    parser = argparse.ArgumentParser(description="Download additional legal books")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    progress = load_progress()

    if args.list:
        for book in ADDITIONAL_BOOKS:
            exists = (BOOKS_DIR / book.filename).exists()
            status = "YES" if exists else "NO"
            print(f"  [{status}] {book.filename} - {book.title}")
        return

    print(f"Downloading {len(ADDITIONAL_BOOKS)} additional legal books...")
    print(f"Target: {BOOKS_DIR}\n")

    ok = 0
    fail = 0
    skip = 0

    for i, book in enumerate(ADDITIONAL_BOOKS, 1):
        dest = BOOKS_DIR / book.filename
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"[{i}/{len(ADDITIONAL_BOOKS)}] SKIP  {book.filename} (exists)")
            skip += 1
            continue

        print(
            f"[{i}/{len(ADDITIONAL_BOOKS)}] GET   {book.filename}...",
            end=" ",
            flush=True,
        )
        success = download_book(book, progress, dry_run=args.dry_run)

        if success:
            size_kb = dest.stat().st_size / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok += 1
        else:
            print("FAILED")
            fail += 1

        time.sleep(1)  # polite delay

    print(f"\nDone: {ok} downloaded, {skip} skipped, {fail} failed")
    print(f"Total books now: {len(list(BOOKS_DIR.glob('*.pdf')))}")


if __name__ == "__main__":
    main()
