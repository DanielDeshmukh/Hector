import os
os.environ["HECTOR_TESSERACT_CMD"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["HECTOR_POPPLER_PATH"] = r"C:\Users\DANIEL\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"

from utils.enhanced_ingestor import EnhancedHectorIngestor

print("Starting re-indexing with section-aware chunker...")
ingestor = EnhancedHectorIngestor(reindex_mode=True)
ingestor.run()
print("Done!")
