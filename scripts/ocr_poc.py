"""OCR single PDF: Prevention_of_Corruption_Act_1988.pdf."""
import subprocess
import os
import tempfile
from pathlib import Path

books = Path(r"D:\Vs Code\VS code\Hector\data\Books")
pdf = books / "Prevention_of_Corruption_Act_1988.pdf"
tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

with tempfile.TemporaryDirectory() as tmpdir:
    prefix = os.path.join(tmpdir, "poc")
    r = subprocess.run(
        ["pdftoppm", "-png", "-r", "200", str(pdf), prefix],
        capture_output=True, timeout=300,
    )
    if r.returncode != 0:
        print("pdftoppm failed")
        exit(1)

    images = sorted(Path(tmpdir).glob("poc-*.png"))
    print(f"Processing {len(images)} pages...")

    texts = []
    for i, img in enumerate(images, 1):
        r = subprocess.run(
            [tess, str(img), "stdout", "-l", "eng", "--psm", "6"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
        )
        t = r.stdout.decode("utf-8", errors="replace").strip()
        if t:
            texts.append(f"--- Page {i} ---\n{t}")
        if i % 10 == 0:
            print(f"  Page {i}/{len(images)} done")

    full = "\n\n".join(texts)
    out = books / "Prevention_of_Corruption_Act_1988.txt"
    out.write_text(full, encoding="utf-8")
    print(f"Done: {len(full.split())} words, {len(full)} chars")
