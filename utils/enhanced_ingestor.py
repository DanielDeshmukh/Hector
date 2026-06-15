import hashlib
import os
import time
import uuid
from datetime import datetime
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "0")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

# Import the legal structure parser
from utils.legal_structure_parser import LegalStructureParser, MetadataEnricher

# Optional OCR dependencies
try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

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
PDF_RENDER_DPI = 300

if HAS_OCR:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
POPPLER_PATH = POPPLER_PATH or None

console = Console()


class EnhancedHectorIngestor:
    """
    Enhanced Ingestor with Legal Structure Parsing.

    Features:
    - Extracts hierarchical legal metadata (Act > Chapter > Section)
    - Detects illustrations, exceptions, "Provided that" clauses
    - Identifies structure type (bare_act, commentary, etc.)
    - Adds comprehensive metadata for better retrieval
    """

    def __init__(self, reindex_mode=False):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.embedding_fn = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="indian_law_bns",
            embedding_function=self.embedding_fn,
        )
        self.parser = LegalStructureParser()
        self.enricher = MetadataEnricher()
        self.session_processed_pages = 0
        self.reindex_mode = reindex_mode
        self.stats = {
            "pages_processed": 0,
            "chunks_created": 0,
            "acts_found": set(),
            "sections_found": 0,
            "structure_types": {}
        }

    def get_page_hash(self, filename: str, pg_num: int) -> str:
        """Generate a stable fingerprint for a source page."""
        return hashlib.md5(f"{filename}_{pg_num}".encode()).hexdigest()

    def cooldown_timer(self, minutes: int = 5, reason: str = "API Rate Limit"):
        """Display a countdown during enforced cooldown."""
        console.print(f"[yellow]Cooldown: {reason} ({minutes} min)...[/yellow]")
        time.sleep(minutes * 60)

    def tokenize_text(self, text: str) -> list[str]:
        """Simple whitespace tokenization."""
        return text.split()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = CHUNK_SIZE_TOKENS,
        overlap: int = CHUNK_OVERLAP_TOKENS
    ) -> list[str]:
        """Build overlapping token windows preserving legal context."""
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

    def extract_text_from_image(self, image) -> str:
        """Run Tesseract OCR on rendered PDF page."""
        if not HAS_OCR:
            return ""
        return pytesseract.image_to_string(image, lang="eng").strip()

    def build_chunk_payloads(
        self,
        text: str,
        filename: str,
        page_number: int,
        page_hash: str
    ) -> tuple[list[str], list[dict], list[str]]:
        """
        Build chunk documents with enhanced legal metadata.

        Parses document structure and enriches each chunk with:
        - act_name, chapter, section_number
        - is_bns, is_ipc, is_repealed
        - has_illustration, has_exception, has_provided_that
        - structure_type
        """
        chunk_texts = self.chunk_text(text)
        if not chunk_texts:
            return [], [], []

        # Parse document structure once per page
        structure = self.parser.parse_document(text, filename)

        # Track stats
        if structure.get("act"):
            self.stats["acts_found"].add(structure["act"])
        if structure.get("section"):
            self.stats["sections_found"] += 1
        struct_type = structure.get("structure_type", "unknown")
        self.stats["structure_types"][struct_type] = \
            self.stats["structure_types"].get(struct_type, 0) + 1

        ingested_at = str(datetime.now())
        documents = []
        metadatas = []
        ids = []

        for chunk_index, chunk in enumerate(chunk_texts):
            documents.append(chunk)

            # Build base metadata
            base_metadata = {
                "source": filename,
                "page": page_number,
                "page_hash": page_hash,
                "chunk_index": chunk_index,
                "ingested_at": ingested_at,
                "mapping_accuracy": "enhanced_v1" if not self.reindex_mode else "reindex_v1",
            }

            # Enrich with legal structure metadata
            enriched_metadata = self.enricher.enrich_metadata(
                base_metadata, structure, filename
            )

            metadatas.append(enriched_metadata)
            ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    def maybe_take_session_air_break(self):
        """Enforce cooldown every 400 pages."""
        if self.session_processed_pages == 0:
            return
        if self.session_processed_pages % SESSION_AIR_BREAK_PAGES != 0:
            return

        console.print(f"\n[yellow]Session break after {self.session_processed_pages} pages...[/yellow]")
        self.cooldown_timer(minutes=SESSION_AIR_BREAK_MINUTES, reason="Session air break")

    def process_single_page(
        self,
        file_path: str,
        filename: str,
        pg_num: int
    ) -> dict[str, Any]:
        """Process a single page and return results."""
        page_hash = self.get_page_hash(filename, pg_num)

        # Check for duplicates
        if not self.reindex_mode:
            existing = self.collection.get(where={"page_hash": page_hash})
            if existing["ids"]:
                return {"status": "skipped", "reason": "duplicate", "chunks": 0}

        try:
            # Try pypdf text extraction first
            text = ""
            try:
                reader = PdfReader(file_path)
                if pg_num <= len(reader.pages):
                    page = reader.pages[pg_num - 1]
                    text = page.extract_text() or ""
                    text = text.strip()
            except Exception:
                pass

            # Fall back to OCR for scanned PDFs
            if (not text or len(text.strip()) < 20) and HAS_OCR:
                try:
                    page_images = convert_from_path(
                        file_path,
                        dpi=PDF_RENDER_DPI,
                        first_page=pg_num,
                        last_page=pg_num,
                        poppler_path=POPPLER_PATH
                    )
                    if page_images:
                        text = self.extract_text_from_image(page_images[0])
                except Exception:
                    pass

            if not text or len(text.strip()) < 20:
                return {"status": "skipped", "reason": "empty_page", "chunks": 0}

            documents, metadatas, ids = self.build_chunk_payloads(
                text=text,
                filename=filename,
                page_number=pg_num,
                page_hash=page_hash,
            )

            if documents:
                self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
                self.stats["pages_processed"] += 1
                self.stats["chunks_created"] += len(documents)

                return {"status": "success", "chunks": len(documents), "text_preview": text[:100]}

            return {"status": "skipped", "reason": "no_chunks", "chunks": 0}

        except Exception as e:
            return {"status": "error", "reason": str(e), "chunks": 0}

    def process_book(self, filename: str, file_path: str) -> dict[str, Any]:
        """Process all pages in a single book."""
        console.print(f"\n[bold cyan]Processing:[/bold cyan] {filename}")

        # Get total page count from pypdf
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
        except Exception:
            total_pages = 9999

        pg_num = 1
        pages_in_book = 0
        chunks_in_book = 0

        while pg_num <= total_pages:
            result = self.process_single_page(file_path, filename, pg_num)

            if result["status"] == "finished":
                break
            elif result["status"] == "error":
                console.print(f"  [red]Error page {pg_num}:[/red] {result['reason']}")
                break
            elif result["status"] == "success":
                pages_in_book += 1
                chunks_in_book += result["chunks"]

            pg_num += 1
            self.session_processed_pages += 1

            if pg_num % 50 == 0:
                self.maybe_take_session_air_break()

        return {
            "filename": filename,
            "pages": pages_in_book,
            "chunks": chunks_in_book
        }

    def display_stats(self):
        """Display ingestion statistics."""
        table = Table(title="Ingestion Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Pages Processed", str(self.stats["pages_processed"]))
        table.add_row("Chunks Created", str(self.stats["chunks_created"]))
        table.add_row("Sections Found", str(self.stats["sections_found"]))
        table.add_row("Acts Identified", ", ".join(sorted(self.stats["acts_found"])))

        if self.stats["structure_types"]:
            struct_row = ", ".join(
                f"{k}: {v}" for k, v in self.stats["structure_types"].items()
            )
            table.add_row("Structure Types", struct_row)

        console.print(table)

    def run(self):
        """Main ingestion loop."""
        if not os.path.exists(BOOKS_DIR):
            console.print(f"[red]Error: Books directory not found:[/red] {BOOKS_DIR}")
            return

        files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf")]

        if not files:
            console.print(f"[yellow]No PDF files found in:[/yellow] {BOOKS_DIR}")
            return

        mode_text = "[yellow]RE-INDEX[/yellow]" if self.reindex_mode else "[green]NEW[/green]"
        console.print(f"\n[bold]Enhanced Ingestor[/bold] | Mode: {mode_text} | Books: {len(files)}")

        book_results = []
        for index, filename in enumerate(files):
            file_path = os.path.join(BOOKS_DIR, filename)
            result = self.process_book(filename, file_path)
            book_results.append(result)
            console.print(
                f"  [green]✓[/green] {filename}: {result['pages']} pages, "
                f"{result['chunks']} chunks"
            )

        # Final stats
        console.print("\n[bold green]FINAL SUMMARY[/bold green]")
        self.display_stats()

        console.print(f"\n[bold]Total records in DB:[/bold] {self.collection.count()}")


def create_reindex_tool():
    """Create a utility to re-index existing documents with new metadata."""
    console = Console()

    console.print("\n[bold yellow]Re-Index Mode:[/bold yellow] This will add enhanced metadata")
    console.print("to existing documents without duplicating content.\n")

    confirm = console.input("Continue? (y/n): ")
    if confirm.lower() == 'y':
        ingestor = EnhancedHectorIngestor(reindex_mode=True)
        ingestor.run()
    else:
        console.print("[yellow]Re-index cancelled.[/yellow]")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--reindex":
        create_reindex_tool()
    else:
        EnhancedHectorIngestor(reindex_mode=False).run()
