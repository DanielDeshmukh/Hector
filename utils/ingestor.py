import hashlib
import os
import time
import uuid
from datetime import datetime

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb
import pytesseract
from dotenv import load_dotenv
from pdf2image import convert_from_path
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = os.getenv("HECTOR_BOOKS_DIR", os.path.join(PROJECT_ROOT, "data", "Books"))
DB_PATH = os.getenv("HECTOR_DB_PATH", os.path.join(PROJECT_ROOT, "hector_db"))
POPPLER_PATH = os.getenv("HECTOR_POPPLER_PATH", "")
TESSERACT_CMD = os.getenv("HECTOR_TESSERACT_CMD", "tesseract")

CHUNK_SIZE_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 150
SESSION_AIR_BREAK_PAGES = 400
SESSION_AIR_BREAK_MINUTES = 5
INTER_BOOK_COOLDOWN_MINUTES = 10
PDF_RENDER_DPI = 300

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
POPPLER_PATH = POPPLER_PATH or None

console = Console()


class HectorIngestor:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.embedding_fn = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="indian_law_bns",
            embedding_function=self.embedding_fn,
        )
        self.session_processed_pages = 0

    def get_page_hash(self, filename, pg_num):
        """Generate a stable fingerprint for a source page."""
        return hashlib.md5(f"{filename}_{pg_num}".encode()).hexdigest()

    def cooldown_timer(self, minutes=15, reason="Resting OCR Pipeline"):
        """Display a countdown clock during enforced cooldown windows."""
        seconds = minutes * 60
        with Live(auto_refresh=True, console=console) as live:
            while seconds > 0:
                mins, secs = divmod(seconds, 60)
                timer_text = Text(f"{mins:02d}:{secs:02d}", style="bold yellow", justify="center")
                live.update(
                    Panel(
                        timer_text,
                        title="[bold red]Cooldown in Progress[/bold red]",
                        subtitle=reason,
                    )
                )
                time.sleep(1)
                seconds -= 1
        console.print("[bold green]Cooldown Complete. Resuming Ingestion...[/bold green]")

    def tokenize_text(self, text):
        """Tokenize OCR output with a simple whitespace strategy."""
        return text.split()

    def chunk_text(self, text, chunk_size=CHUNK_SIZE_TOKENS, overlap=CHUNK_OVERLAP_TOKENS):
        """Build overlapping token windows so legal context survives chunk boundaries."""
        words = self.tokenize_text(text)
        if not words:
            return []

        chunks = []
        index = 0
        step = max(chunk_size - overlap, 1)

        while index < len(words):
            chunk = " ".join(words[index:index + chunk_size])
            if chunk:
                chunks.append(chunk)
            index += step
            if index >= len(words):
                break

        return chunks

    def extract_text_from_image(self, image):
        """Run local Tesseract OCR on a single rendered PDF page."""
        return pytesseract.image_to_string(image, lang="eng").strip()

    def build_chunk_payloads(self, text, filename, page_number, page_hash):
        """Buffer chunk documents and metadata so each page writes in one Chroma call."""
        chunk_texts = self.chunk_text(text)
        if not chunk_texts:
            return [], [], []

        ingested_at = str(datetime.now())
        documents = []
        metadatas = []
        ids = []

        for chunk_index, chunk in enumerate(chunk_texts):
            documents.append(chunk)
            metadatas.append(
                {
                    "source": filename,
                    "page": page_number,
                    "page_hash": page_hash,
                    "chunk_index": chunk_index,
                    "ingested_at": ingested_at,
                    "mapping_accuracy": "detailed_scan_v3",
                }
            )
            ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    def maybe_take_session_air_break(self):
        """Enforce a 5-minute cooling window every 400 processed pages in this run."""
        if self.session_processed_pages == 0:
            return
        if self.session_processed_pages % SESSION_AIR_BREAK_PAGES != 0:
            return

        console.print(
            f"\n[bold yellow]{self.session_processed_pages} pages processed this session.[/bold yellow] "
            f"Triggering mandatory API air break..."
        )
        self.cooldown_timer(
            minutes=SESSION_AIR_BREAK_MINUTES,
            reason="Mandatory API Air Break",
        )

    def process_with_heartbeat(self):
        # 1. Verify Directory
        if not os.path.exists(BOOKS_DIR):
            console.print(f"[bold red]Error:[/bold red] Directory not found: {BOOKS_DIR}")
            return

        files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf")]
        
        if not files:
            console.print(f"[bold yellow]No PDF files found in:[/bold yellow] {BOOKS_DIR}")
            return

        try:
            for index, filename in enumerate(files):
                file_path = os.path.join(BOOKS_DIR, filename)
                console.print(f"\n[bold magenta]BOOK {index + 1}/{len(files)}[/bold magenta] | [cyan]{filename}[/cyan]")

                # Loop through pages one by one
                pg_num = 1
                while True:
                    page_hash = self.get_page_hash(filename, pg_num)

                    # Check for duplicates
                    existing = self.collection.get(where={"page_hash": page_hash})
                    if existing["ids"]:
                        # Silent skip for speed, or console.print if you want to see progress
                        pg_num += 1
                        continue

                    try:
                        # Process one page at a time
                        page_images = convert_from_path(
                            file_path,
                            dpi=PDF_RENDER_DPI,
                            first_page=pg_num,
                            last_page=pg_num,
                            poppler_path=POPPLER_PATH
                        )
                        
                        if not page_images:
                            break # Reached end of PDF
                            
                        page_image = page_images[0]
                        text = self.extract_text_from_image(page_image)

                        if text:
                            documents, metadatas, ids = self.build_chunk_payloads(
                                text=text,
                                filename=filename,
                                page_number=pg_num,
                                page_hash=page_hash,
                            )

                            if documents:
                                self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
                                console.print(f"  [green]+[/green] Ingested Page {pg_num} ({len(documents)} chunks)")
                        
                        pg_num += 1
                        self.session_processed_pages += 1
                        self.maybe_take_session_air_break()

                    except Exception as page_err:
                        # This usually triggers when pg_num exceeds total pages
                        break 

        except Exception as e:
            console.print(f"[bold red]Critical Error:[/bold red] {e}")
        finally:
            console.print(f"\n[bold green]INGESTION SUMMARY[/bold green]")
            console.print(f"Total Unique Records in DB: [cyan]{self.collection.count()}[/cyan]")

if __name__ == "__main__":
    HectorIngestor().process_with_heartbeat()
