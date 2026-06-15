"""
HECTOR Legal Corpus Downloader
Downloads Tier 1-3 legal PDFs from official Indian government sources.

Usage:
    python scripts/download_books.py              # Download all tiers
    python scripts/download_books.py --tier 1     # Download only Tier 1
    python scripts/download_books.py --list       # List all books and status
    python scripts/download_books.py --dry-run    # Show URLs without downloading
"""

import argparse
import hashlib
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "Books"


@dataclass
class LegalBook:
    tier: int
    filename: str
    title: str
    short_name: str
    urls: list[str]  # Multiple source URLs (fallback chain)
    sha256: str | None = None  # Optional checksum for verification
    description: str = ""


# fmt: off
LEGAL_BOOKS: list[LegalBook] = [
    # ── Tier 1: Core Criminal Law ──────────────────────────────────────
    LegalBook(
        tier=1,
        filename="Indian_Penal_Code_1860.pdf",
        title="Indian Penal Code, 1860",
        short_name="IPC",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2088/1/A1860-45.pdf",
            "https://legislative.gov.in/sites/default/files/A1860-45.pdf",
        ],
        description="The original penal code of India, now largely superseded by BNS",
    ),
    LegalBook(
        tier=1,
        filename="Bharatiya_Nyaya_Sanhita_2023.pdf",
        title="Bharatiya Nyaya Sanhita, 2023",
        short_name="BNS",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/3688/1/Bharatiya_Nyaya_Sanhita_2023.pdf",
            "https://legislative.gov.in/sites/default/files/2023-21.pdf",
        ],
        description="The new criminal code replacing IPC, effective July 1 2024",
    ),
    LegalBook(
        tier=1,
        filename="Code_of_Criminal_Procedure_1973.pdf",
        title="Code of Criminal Procedure, 1973",
        short_name="CrPC",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/1526/1/A1973-02.pdf",
            "https://legislative.gov.in/sites/default/files/A1973-02.pdf",
        ],
        description="Procedural law for criminal trials in India",
    ),
    LegalBook(
        tier=1,
        filename="Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf",
        title="Bharatiya Nagarik Suraksha Sanhita, 2023",
        short_name="BNSS",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/3701/1/Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf",
        ],
        description="The new criminal procedure code replacing CrPC",
    ),
    LegalBook(
        tier=1,
        filename="Indian_Evidence_Act_1872.pdf",
        title="Indian Evidence Act, 1872",
        short_name="IEA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/1589/1/A1872-01.pdf",
            "https://legislative.gov.in/sites/default/files/A1872-01.pdf",
        ],
        description="The original evidence law of India",
    ),
    LegalBook(
        tier=1,
        filename="Bharatiya_Sakshya_Adhiniyam_2023.pdf",
        title="Bharatiya Sakshya Adhiniyam, 2023",
        short_name="BSA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/3702/1/Bharatiya_Sakshya_Adhiniyam_2023.pdf",
        ],
        description="The new evidence act replacing Indian Evidence Act",
    ),

    # ── Tier 2: Constitutional & Supporting Acts ──────────────────────
    LegalBook(
        tier=2,
        filename="Constitution_of_India.pdf",
        title="Constitution of India",
        short_name="Constitution",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2163/1/Constitution_of_India.pdf",
            "https://legislative.gov.in/sites/default/files/Constitution_of_India.pdf",
        ],
        description="Supreme law of India with fundamental rights and constitutional remedies",
    ),
    LegalBook(
        tier=2,
        filename="Indian_Contract_Act_1872.pdf",
        title="Indian Contract Act, 1872",
        short_name="ICA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/1672/1/A1872-09.pdf",
        ],
        description="Governs contracts, breach, and fraud in India",
    ),
    LegalBook(
        tier=2,
        filename="Negotiable_Instruments_Act_1881.pdf",
        title="Negotiable Instruments Act, 1881",
        short_name="NI Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/1944/1/A1881-26.pdf",
        ],
        description="Cheque bounce offences under Section 138 - most filed case in India",
    ),
    LegalBook(
        tier=2,
        filename="Transfer_of_Property_Act_1882.pdf",
        title="Transfer of Property Act, 1882",
        short_name="TPA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/1955/1/A1882-04.pdf",
        ],
        description="Property offences and criminal breach of trust",
    ),
    LegalBook(
        tier=2,
        filename="Specific_Relief_Act_1963.pdf",
        title="Specific Relief Act, 1963",
        short_name="SRA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2090/1/A1963-47.pdf",
        ],
        description="Injunctions and specific performance of contracts",
    ),
    LegalBook(
        tier=2,
        filename="Limitation_Act_1963.pdf",
        title="Limitation Act, 1963",
        short_name="LA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2091/1/A1963-36.pdf",
        ],
        description="Time bars for filing legal proceedings",
    ),

    # ── Tier 3: Special Criminal Laws ─────────────────────────────────
    LegalBook(
        tier=3,
        filename="Prevention_of_Corruption_Act_1988.pdf",
        title="Prevention of Corruption Act, 1988",
        short_name="PCA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2394/1/A1988-49.pdf",
        ],
        description="Public servant offences and corruption",
    ),
    LegalBook(
        tier=3,
        filename="Information_Technology_Act_2000.pdf",
        title="Information Technology Act, 2000",
        short_name="IT Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2397/1/A2000-21.pdf",
        ],
        description="Cybercrime, electronic evidence, and digital offences",
    ),
    LegalBook(
        tier=3,
        filename="Protection_of_Women_from_Domestic_Violence_Act_2005.pdf",
        title="Protection of Women from Domestic Violence Act, 2005",
        short_name="DV Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2688/1/A2005-43.pdf",
        ],
        description="Domestic violence protections and offences",
    ),
    LegalBook(
        tier=3,
        filename="Juvenile_Justice_Act_2015.pdf",
        title="Juvenile Justice (Care and Protection of Children) Act, 2015",
        short_name="JJ Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2752/1/A2015-02.pdf",
        ],
        description="Juvenile offenders and child protection",
    ),
    LegalBook(
        tier=3,
        filename="Arms_Act_1959.pdf",
        title="Arms Act, 1959",
        short_name="Arms Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/755/1/A1959-54.pdf",
        ],
        description="Weapons offences and licensing",
    ),
    LegalBook(
        tier=3,
        filename="Narcotic_Drugs_and_Psychotropic_Substances_Act_1985.pdf",
        title="Narcotic Drugs and Psychotropic Substances Act, 1985",
        short_name="NDPS",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2312/1/A1985-61.pdf",
        ],
        description="Drug offences and controlled substances",
    ),
    LegalBook(
        tier=3,
        filename="Motor_Vehicles_Act_1988.pdf",
        title="Motor Vehicles Act, 1988",
        short_name="MV Act",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/2133/1/A1988-59.pdf",
        ],
        description="Road accident offences, hit and run, traffic violations",
    ),
    LegalBook(
        tier=3,
        filename="Consumer_Protection_Act_2019.pdf",
        title="Consumer Protection Act, 2019",
        short_name="CPA",
        urls=[
            "https://www.indiacode.nic.in/bitstream/123456789/3346/1/A2019-35.pdf",
        ],
        description="Consumer fraud and deficiency in service",
    ),
]
# fmt: on


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_existing_books() -> dict[str, Path]:
    """Return map of filename -> path for PDFs already in Books dir."""
    existing = {}
    if BOOKS_DIR.exists():
        for f in BOOKS_DIR.glob("*.pdf"):
            existing[f.name] = f
    return existing


def download_file(url: str, dest: Path, timeout: int = 120) -> bool:
    """Download a file with progress reporting. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HECTOR-LegalBot/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            dest.parent.mkdir(parents=True, exist_ok=True)

            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r    [{pct:3d}%] {downloaded / 1048576:.1f} / {total / 1048576:.1f} MB", end="", flush=True)
                    else:
                        print(f"\r    [{downloaded / 1048576:.1f} MB downloaded]", end="", flush=True)
            print()  # newline after progress
        return True
    except Exception as e:
        print(f"\n    [ERROR] {e}")
        if dest.exists():
            dest.unlink()
        return False


def cmd_list():
    """List all books and their download status."""
    existing = get_existing_books()

    print(f"\n{'Tier':<6} {'Status':<10} {'Filename':<50} {'Title'}")
    print("-" * 120)

    for book in LEGAL_BOOKS:
        found = book.filename in existing
        status = "[OK]" if found else "[  ]"
        size = ""
        if found:
            size_mb = existing[book.filename].stat().st_size / 1048576
            size = f" ({size_mb:.1f} MB)"
        print(f"  {book.tier:<4} {status:<10} {book.filename:<50} {book.title}{size}")

    downloaded = sum(1 for b in LEGAL_BOOKS if b.filename in existing)
    print(f"\nTotal: {downloaded}/{len(LEGAL_BOOKS)} books present in {BOOKS_DIR}")


def cmd_download(tier: int | None = None, dry_run: bool = False):
    """Download books for specified tier(s)."""
    existing = get_existing_books()
    to_download = [b for b in LEGAL_BOOKS if b.filename not in existing]

    if tier is not None:
        to_download = [b for b in to_download if b.tier == tier]

    if not to_download:
        print("\nAll books for the requested tier(s) are already downloaded.")
        return

    print(f"\nBooks to download: {len(to_download)}")
    for book in to_download:
        print(f"  Tier {book.tier}: {book.title}")

    if dry_run:
        print("\n[DRY RUN] URLs that would be fetched:")
        for book in to_download:
            print(f"\n  {book.filename}:")
            for url in book.urls:
                print(f"    {url}")
        return

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    failed = 0
    for book in to_download:
        print(f"\n{'=' * 60}")
        print(f"  [{book.tier}] {book.title}")
        print(f"  File: {book.filename}")

        downloaded = False
        for url in book.urls:
            print(f"  Trying: {url[:80]}...")
            dest = BOOKS_DIR / book.filename
            if download_file(url, dest):
                size_mb = dest.stat().st_size / 1048576
                if size_mb < 0.01:
                    print(f"  [WARN] File too small ({size_mb * 1024:.0f} KB) — likely an error page, trying next URL")
                    dest.unlink()
                    continue
                print(f"  [OK] Downloaded: {size_mb:.1f} MB")
                succeeded += 1
                downloaded = True
                break
            time.sleep(1)  # polite delay between attempts

        if not downloaded:
            print(f"  [FAIL] Could not download from any source")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {succeeded} succeeded, {failed} failed")
    print(f"  Books directory: {BOOKS_DIR}")

    if succeeded > 0:
        print(f"\n  Next step: Run 'python main.py ingest' to index the new books")


def main():
    parser = argparse.ArgumentParser(
        description="HECTOR Legal Corpus Downloader — fetch bare acts from legislative.gov.in",
    )
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Download only a specific tier (1=core, 2=supporting, 3=special)")
    parser.add_argument("--list", action="store_true", help="List all books and download status")
    parser.add_argument("--dry-run", action="store_true", help="Show URLs without downloading")

    args = parser.parse_args()

    if args.list:
        cmd_list()
    else:
        cmd_download(tier=args.tier, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
