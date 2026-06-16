"""OCR scanned PDFs using Tesseract + Poppler (pdf2image)."""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "Books"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# PDFs that need OCR (extracted 0 text)
SCANNED_PDFS = [
    "Family_Courts_Act_1984.pdf",
    "Gram_Nyayalayas_Act_2008.pdf",
    "Juvenile_Justice_Act_2015.pdf",
    "Prevention_of_Corruption_Act_1988.pdf",
]


def ocr_pdf(pdf_path: Path, output_dir: Path, lang: str = "eng") -> str:
    """Convert scanned PDF to text using pdftoppm + tesseract."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = pdf_path.stem

    # Step 1: Convert PDF pages to images using pdftoppm
    img_prefix = output_dir / base_name
    result = subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r", "300",  # 300 DPI for good OCR
            str(pdf_path),
            str(img_prefix),
        ],
        capture_output=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftoppm failed: {result.stderr.decode('utf-8', errors='replace')}")

    # Step 2: OCR each image with Tesseract
    all_text = []
    images = sorted(output_dir.glob(f"{base_name}-*.png"))

    for img_path in images:
        result = subprocess.run(
            [
                TESSERACT_CMD,
                str(img_path),
                "stdout",
                "-l", lang,
                "--psm", "6",  # Assume uniform block of text
                "--oem", "3",  # Default OCR engine
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        page_text = result.stdout.decode("utf-8", errors="replace").strip()
        if page_text:
            all_text.append(f"--- Page {len(all_text) + 1} ---\n{page_text}")

    # Step 3: Save as .txt alongside the PDF
    txt_path = pdf_path.with_suffix(".txt")
    full_text = "\n\n".join(all_text)
    txt_path.write_text(full_text, encoding="utf-8")

    # Step 4: Clean up images
    for img_path in images:
        img_path.unlink(missing_ok=True)

    return full_text


def main():
    print("OCR Scanner for HECTOR scanned PDFs")
    print(f"Tesseract: {TESSERACT_CMD}")
    print(f"Books dir: {BOOKS_DIR}\n")

    for pdf_name in SCANNED_PDFS:
        pdf_path = BOOKS_DIR / pdf_name
        if not pdf_path.exists():
            print(f"SKIP {pdf_name} (not found)")
            continue

        print(f"OCR  {pdf_name}...", end=" ", flush=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                text = ocr_pdf(pdf_path, Path(tmpdir))
                words = len(text.split())
                chars = len(text)
                print(f"OK ({words} words, {chars} chars)")
            except Exception as e:
                print(f"FAILED: {e}")

    # Summary
    print("\n--- Summary ---")
    for pdf_name in SCANNED_PDFS:
        txt_path = BOOKS_DIR / pdf_name.replace(".pdf", ".txt")
        if txt_path.exists():
            content = txt_path.read_text(encoding="utf-8")
            words = len(content.split())
            has_section = "section" in content.lower()
            quality = "GOOD" if words > 100 and has_section else "PARTIAL"
            print(f"  {pdf_name:<45} {words:>5} words  {quality}")
        else:
            print(f"  {pdf_name:<45} NO TXT FILE")


if __name__ == "__main__":
    main()
