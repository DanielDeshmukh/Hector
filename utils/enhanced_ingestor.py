import hashlib
import logging
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "0")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
from rich.console import Console
from rich.table import Table

# Import the legal structure parser
from utils.legal_structure_parser import LegalStructureParser, MetadataEnricher

logger = logging.getLogger("hector.ingest")

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
MIN_CHUNK_CHARS = 50
PAGE_EXTRACTION_TIMEOUT = 30  # seconds per page

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

        # Use embedding provider abstraction if available
        try:
            from core.embedding_provider import get_embedding_provider
            provider = os.getenv("HECTOR_EMBEDDING_PROVIDER", "local")
            embedder = get_embedding_provider(provider)
            self.embedding_fn = embedder.get_chroma_embedding_function()
        except (ImportError, Exception):
            # Fall back to default local embedding
            self.embedding_fn = (
                chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            )

        self.collection = self.client.get_or_create_collection(
            name=f"indian_law_bns_{provider}",
            embedding_function=self.embedding_fn,
        )
        self.parser = LegalStructureParser()
        self.enricher = MetadataEnricher()
        self.session_processed_pages = 0
        self.reindex_mode = reindex_mode
        self.verbose = os.getenv("HECTOR_INGEST_VERBOSE") == "1"
        self.stats = {
            "pages_processed": 0,
            "chunks_created": 0,
            "chunks_rejected": 0,
            "acts_found": [],
            "sections_found": 0,
            "structure_types": {},
        }
        # Track progress for ETA calculation
        self._total_books = 0
        self._current_book_index = 0
        self._book_start_time = 0.0
        self._total_pages_estimated = 0
        self._pages_processed_session = 0
        # Resume state: track completed books + per-page progress
        self._resume_file = os.path.join(DB_PATH, ".ingest_resume.json")
        resume_data = self._load_resume_state()
        self._completed_books = resume_data.get("completed", set())
        self._book_pages_done = resume_data.get("book_pages", {})

    def get_page_hash(self, filename: str, pg_num: int) -> str:
        """Generate a stable fingerprint for a source page."""
        return hashlib.md5(f"{filename}_{pg_num}".encode()).hexdigest()

    def get_content_hash(self, text: str) -> str:
        """Generate a content hash for deduplication."""
        return hashlib.sha256(text.strip().encode()).hexdigest()[:16]

    def _load_resume_state(self) -> dict:
        """Load resume state: completed books + per-page progress."""
        import json

        if os.path.exists(self._resume_file):
            try:
                with open(self._resume_file) as f:
                    data = json.load(f)
                return {
                    "completed": set(data.get("completed", [])),
                    "book_pages": data.get("book_pages", {}),
                }
            except Exception:
                pass
        return {"completed": set(), "book_pages": {}}

    def _save_resume_state(self):
        """Persist completed book list and per-page progress to disk."""
        import json

        os.makedirs(os.path.dirname(self._resume_file), exist_ok=True)
        with open(self._resume_file, "w") as f:
            json.dump(
                {
                    "completed": list(self._completed_books),
                    "book_pages": self._book_pages_done,
                },
                f,
            )

    def _mark_book_complete(self, filename: str):
        """Mark a book as fully ingested for resume support."""
        self._completed_books.add(filename)
        # Clean up per-page state for completed book
        self._book_pages_done.pop(filename, None)
        self._save_resume_state()

    def _mark_page_done(self, filename: str, pg_num: int):
        """Record that a specific page has been processed."""
        if filename not in self._book_pages_done:
            self._book_pages_done[filename] = []
        if pg_num not in self._book_pages_done[filename]:
            self._book_pages_done[filename].append(pg_num)
        # Save every 10 pages to avoid excessive I/O
        if len(self._book_pages_done[filename]) % 10 == 0:
            self._save_resume_state()

    def _get_book_pages_done(self, filename: str) -> set[int]:
        """Get set of page numbers already processed for a book."""
        return set(self._book_pages_done.get(filename, []))

    def cooldown_timer(self, minutes: int = 5, reason: str = "API Rate Limit"):
        """Display a countdown during enforced cooldown."""
        console.print(f"[yellow]Cooldown: {reason} ({minutes} min)...[/yellow]")
        time.sleep(minutes * 60)

    def validate_pdf(self, file_path: str, filename: str) -> tuple[bool, str]:
        """
        Validate PDF file before processing.

        Checks:
        - File exists and is non-empty
        - File header starts with %PDF
        - File is not encrypted
        - Page count is reasonable (> 0)

        Returns:
            (is_valid, error_message)
        """
        # Check file exists and has content
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"File is empty: {filename}"

        if file_size < 100:
            return False, f"File too small ({file_size} bytes), likely corrupted: {filename}"

        # Check PDF header (first 5 bytes should be %PDF)
        try:
            with open(file_path, "rb") as f:
                header = f.read(5)
            if header[:4] != b"%PDF":
                return False, f"Invalid PDF header (got {header!r}): {filename}"
        except (OSError, IOError) as e:
            return False, f"Cannot read file header: {e}"

        # Try to open with pypdf and check for encryption / page count
        try:
            reader = PdfReader(file_path)
            if reader.is_encrypted:
                return False, f"PDF is encrypted (requires password): {filename}"
            if len(reader.pages) == 0:
                return False, f"PDF has 0 pages: {filename}"
        except Exception as e:
            return False, f"Cannot open PDF with pypdf: {e}"

        return True, ""

    def _run_with_timeout(self, func, *args, timeout: int = PAGE_EXTRACTION_TIMEOUT, **kwargs):
        """
        Run a function with a timeout using ThreadPoolExecutor.

        Args:
            func: Function to execute
            timeout: Maximum seconds to wait
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result of func, or raises TimeoutError
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")

    def tokenize_text(self, text: str) -> list[str]:
        """Simple whitespace tokenization."""
        return text.split()

    # Legal section boundary patterns (used to avoid splitting mid-section)
    SECTION_BOUNDARY_RE = re.compile(
        r"(?:^|\n)(?:Section|Sec\.?|s\.)\s*\d{1,4}[A-Z]?\."
        r"|(?:^|\n)\d{1,4}[A-Z]?\.\s+[A-Z]"
        r"|(?:^|\n)(?:CHAPTER|Chapter|PART|Part)\s+"
        r"(?:IV|III|II|I|V|VI|VII|VIII|IX|X|\d+|[A-Z]+)",
        re.MULTILINE,
    )

    def chunk_text(
        self,
        text: str,
        chunk_size: int = CHUNK_SIZE_TOKENS,
        overlap: int = CHUNK_OVERLAP_TOKENS,
    ) -> list[str]:
        """
        Build overlapping token windows preserving legal context.

        Respects legal section boundaries to avoid splitting mid-section.
        If a chunk boundary falls inside a section, the split point is
        moved to the nearest section boundary.
        """
        words = self.tokenize_text(text)
        if not words:
            return []

        # Find section boundary positions (as word indices)
        boundary_indices = set()
        for match in self.SECTION_BOUNDARY_RE.finditer(text):
            # Convert character position to approximate word index
            char_pos = match.start()
            word_idx = len(text[:char_pos].split())
            if word_idx > 0:
                boundary_indices.add(word_idx)

        chunks = []
        index = 0
        step = max(chunk_size - overlap, 1)

        while index < len(words):
            end_index = min(index + chunk_size, len(words))

            # If we're not at the end, try to find a nearby section boundary
            if end_index < len(words) and boundary_indices:
                # Look for the nearest boundary within the last 20% of the chunk
                search_start = max(index + int(chunk_size * 0.8), index)
                best_boundary = None
                for b in sorted(boundary_indices):
                    if search_start <= b <= end_index:
                        best_boundary = b
                        break
                if best_boundary is not None:
                    end_index = best_boundary

            chunk = " ".join(words[index:end_index])
            if chunk:
                chunks.append(chunk)
            index = end_index
            if index >= len(words):
                break

        return chunks

    def extract_text_from_image(self, image) -> str:
        """Run Tesseract OCR on rendered PDF page."""
        if not HAS_OCR:
            return ""
        return pytesseract.image_to_string(image, lang="eng").strip()

    def _nvidia_ocr_fallback(self, file_path: str, page_number: int) -> str:
        """Use NVIDIA Nemotron OCR API as a final fallback for scanned pages.

        Renders the page to a PNG image via pdf2image, then sends it to the
        NVIDIA Nemotron OCR endpoint. Requires NVIDIA_API_KEY env var.
        Falls back gracefully if the key is missing or the API call fails.
        """
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return ""

        try:
            page_images = convert_from_path(
                file_path,
                dpi=PDF_RENDER_DPI,
                first_page=page_number,
                last_page=page_number,
                poppler_path=POPPLER_PATH,
            )
            if not page_images:
                return ""

            import io, base64
            buf = io.BytesIO()
            page_images[0].save(buf, format="PNG")
            image_b64 = base64.b64encode(buf.getvalue()).decode()

            import requests
            resp = requests.post(
                "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"image": f"data:image/png;base64,{image_b64}"},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("markdown", data.get("text", "")).strip()
        except Exception as e:
            if self.verbose:
                logger.info(f"  NVIDIA OCR fallback failed for page {page_number}: {e}")
            return ""

    def build_chunk_payloads(
        self, text: str, filename: str, page_number: int, page_hash: str
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
        if structure.get("act") and structure["act"] not in self.stats["acts_found"]:
            self.stats["acts_found"].append(structure["act"])
        if structure.get("section"):
            self.stats["sections_found"] += 1
        struct_type = structure.get("structure_type", "unknown")
        self.stats["structure_types"][struct_type] = (
            self.stats["structure_types"].get(struct_type, 0) + 1
        )

        ingested_at = str(datetime.now())
        documents = []
        metadatas = []
        ids = []

        for chunk_index, chunk in enumerate(chunk_texts):
            # Quality gate: reject chunks that are too short
            if len(chunk.strip()) < MIN_CHUNK_CHARS:
                self.stats["chunks_rejected"] += 1
                continue

            documents.append(chunk)

            # Content hash for deduplication
            content_hash = self.get_content_hash(chunk)

            # Check for duplicate content across collection
            if not self.reindex_mode:
                existing = self.collection.get(where={"content_hash": content_hash})
                if existing["ids"]:
                    self.stats["chunks_rejected"] += 1
                    continue

            # Build base metadata
            base_metadata = {
                "source": filename,
                "page": page_number,
                "page_hash": page_hash,
                "content_hash": content_hash,
                "chunk_index": chunk_index,
                "chunk_chars": len(chunk),
                "ingested_at": ingested_at,
                "mapping_accuracy": "enhanced_v1"
                if not self.reindex_mode
                else "reindex_v1",
            }

            # Enrich with legal structure metadata
            enriched_metadata = self.enricher.enrich_metadata(
                base_metadata, structure, filename
            )

            metadatas.append(enriched_metadata)
            ids.append(str(uuid.uuid4()))

            if self.verbose:
                logger.info(
                    f"    chunk {chunk_index}: {len(chunk)} chars, "
                    f"act={enriched_metadata.get('act_name', '?')}, "
                    f"section={enriched_metadata.get('section_number', '?')}, "
                    f"type={enriched_metadata.get('structure_type', '?')}"
                )

        return documents, metadatas, ids

    def maybe_take_session_air_break(self):
        """Enforce cooldown every 400 pages."""
        if self.session_processed_pages == 0:
            return
        if self.session_processed_pages % SESSION_AIR_BREAK_PAGES != 0:
            return

        console.print(
            f"\n[yellow]Session break after {self.session_processed_pages} pages...[/yellow]"
        )
        self.cooldown_timer(
            minutes=SESSION_AIR_BREAK_MINUTES, reason="Session air break"
        )

    def process_single_page(
        self, file_path: str, filename: str, pg_num: int
    ) -> dict[str, Any]:
        """Process a single page and return results."""
        page_hash = self.get_page_hash(filename, pg_num)

        # Check for duplicates
        if not self.reindex_mode:
            existing = self.collection.get(where={"page_hash": page_hash})
            if existing["ids"]:
                if self.verbose:
                    logger.info(f"  Page {pg_num}: skipped (duplicate)")
                return {"status": "skipped", "reason": "duplicate", "chunks": 0}

        try:
            # Try pypdf text extraction first (with timeout)
            text = ""
            try:
                def extract_page_text():
                    reader = PdfReader(file_path)
                    if pg_num <= len(reader.pages):
                        page = reader.pages[pg_num - 1]
                        return (page.extract_text() or "").strip()
                    return ""

                text = self._run_with_timeout(extract_page_text)
            except (TimeoutError, Exception):
                pass

            # Fall back to OCR for scanned PDFs (with timeout)
            if (not text or len(text.strip()) < 20) and HAS_OCR:
                try:
                    def ocr_page():
                        page_images = convert_from_path(
                            file_path,
                            dpi=PDF_RENDER_DPI,
                            first_page=pg_num,
                            last_page=pg_num,
                            poppler_path=POPPLER_PATH,
                        )
                        if page_images:
                            return self.extract_text_from_image(page_images[0])
                        return ""

                    text = self._run_with_timeout(ocr_page, timeout=60)
                except (TimeoutError, Exception):
                    pass

            # Fall back to NVIDIA Nemotron OCR API if local OCR failed
            if not text or len(text.strip()) < 20:
                text = self._nvidia_ocr_fallback(file_path, pg_num)

            if not text or len(text.strip()) < 20:
                if self.verbose:
                    logger.info(f"  Page {pg_num}: skipped (empty/short text)")
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
                if self.verbose:
                    logger.info(
                        f"  Page {pg_num}: {len(documents)} chunks indexed, "
                        f"{len(text)} chars extracted"
                    )

                return {
                    "status": "success",
                    "chunks": len(documents),
                    "text_preview": text[:100],
                }

            return {"status": "skipped", "reason": "no_chunks", "chunks": 0}

        except Exception as e:
            return {"status": "error", "reason": str(e), "chunks": 0}

    def _format_eta(self, seconds: float) -> str:
        """Format seconds into human-readable ETA string."""
        if seconds < 0 or seconds > 86400:
            return "unknown"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def process_txt_book(self, filename: str, file_path: str) -> dict[str, Any]:
        """Process a pre-OCR'd text file as a single book.

        Used for scanned PDFs that were OCR'd externally (e.g., via
        scripts/ocr_scanned_pdfs.py) and saved as .txt alongside the PDF.
        The .txt file is treated as a single continuous page.
        """
        if not self.reindex_mode and filename in self._completed_books:
            console.print(f"  [dim]Skipping {filename} (already ingested)[/dim]")
            logger.info(f"Skipping {filename} (already ingested)")
            return {"filename": filename, "pages": 0, "chunks": 0, "status": "skipped"}

        book_start = time.time()
        self._current_book_index += 1

        console.print(
            f"\n[bold cyan]Processing (OCR text):[/bold cyan] {filename} "
            f"[dim](book {self._current_book_index}/{self._total_books})[/dim]"
        )
        logger.info(
            f"Book {self._current_book_index}/{self._total_books}: "
            f"{filename} (OCR text file)"
        )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception as e:
            console.print(f"  [red]Error reading {filename}: {e}[/red]")
            logger.error(f"Error reading {filename}: {e}")
            return {"filename": filename, "pages": 0, "chunks": 0, "status": "error", "error": str(e)}

        if not text or len(text.strip()) < 20:
            console.print(f"  [red]Skipping {filename}: empty or too short[/red]")
            return {"filename": filename, "pages": 0, "chunks": 0, "status": "empty"}

        # Treat entire text as a single page
        page_hash = self.get_page_hash(filename, 1)

        if not self.reindex_mode:
            existing = self.collection.get(where={"page_hash": page_hash})
            if existing["ids"]:
                console.print(f"  [dim]Skipping {filename} (already indexed)[/dim]")
                return {"filename": filename, "pages": 0, "chunks": 0, "status": "skipped"}

        documents, metadatas, ids = self.build_chunk_payloads(
            text=text,
            filename=filename.replace(".txt", ".pdf"),
            page_number=1,
            page_hash=page_hash,
        )

        chunks_created = 0
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            self.stats["pages_processed"] += 1
            self.stats["chunks_created"] += len(documents)
            chunks_created = len(documents)

        book_elapsed = time.time() - book_start
        console.print(
            f"  [green]Done:[/green] 1 page, "
            f"{chunks_created} chunks in {self._format_eta(book_elapsed)}"
        )
        logger.info(
            f"Book complete (OCR): {filename} — {chunks_created} chunks, "
            f"{self._format_eta(book_elapsed)}"
        )

        if not self.reindex_mode:
            self._mark_book_complete(filename)

        return {
            "filename": filename,
            "pages": 1 if chunks_created > 0 else 0,
            "chunks": chunks_created,
            "elapsed_seconds": round(book_elapsed, 1),
            "status": "completed",
        }

    def process_book(self, filename: str, file_path: str) -> dict[str, Any]:
        """Process all pages in a single book."""
        # Resume: skip books already fully ingested
        if not self.reindex_mode and filename in self._completed_books:
            console.print(f"  [dim]Skipping {filename} (already ingested)[/dim]")
            logger.info(f"Skipping {filename} (already ingested)")
            return {"filename": filename, "pages": 0, "chunks": 0, "status": "skipped"}

        # Validate PDF before processing
        is_valid, error_msg = self.validate_pdf(file_path, filename)
        if not is_valid:
            console.print(f"  [red]Skipping {filename}: {error_msg}[/red]")
            logger.warning(f"Skipping {filename}: {error_msg}")
            return {"filename": filename, "pages": 0, "chunks": 0, "status": "invalid_pdf", "error": error_msg}

        book_start = time.time()
        self._current_book_index += 1

        # Get total page count from pypdf
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
        except Exception:
            total_pages = 9999

        console.print(
            f"\n[bold cyan]Processing:[/bold cyan] {filename} "
            f"[dim]({total_pages} pages, book {self._current_book_index}/{self._total_books})[/dim]"
        )
        logger.info(
            f"Book {self._current_book_index}/{self._total_books}: "
            f"{filename} ({total_pages} pages)"
        )

        pg_num = 1
        pages_in_book = 0
        chunks_in_book = 0
        errors = 0
        pages_done_set = self._get_book_pages_done(filename)
        skipped_resume = 0

        # If resuming, report where we left off
        if pages_done_set and not self.reindex_mode:
            min_done = min(pages_done_set) if pages_done_set else 0
            max_done = max(pages_done_set) if pages_done_set else 0
            console.print(
                f"  [yellow]Resuming: {len(pages_done_set)} pages already indexed "
                f"(pages {min_done}-{max_done})[/yellow]"
            )
            logger.info(
                f"Resuming {filename}: {len(pages_done_set)} pages already indexed"
            )

        while pg_num <= total_pages:
            # Skip pages already processed (unless reindex mode)
            if not self.reindex_mode and pg_num in pages_done_set:
                skipped_resume += 1
                pg_num += 1
                continue

            result = self.process_single_page(file_path, filename, pg_num)

            if result["status"] == "finished":
                break
            elif result["status"] == "error":
                errors += 1
                if errors <= 3:
                    console.print(
                        f"  [red]Error page {pg_num}:[/red] {result['reason']}"
                    )
                break
            elif result["status"] == "success":
                pages_in_book += 1
                chunks_in_book += result["chunks"]
                self._mark_page_done(filename, pg_num)
            elif result["status"] == "skipped":
                # Even skipped pages (duplicates/empty) are marked done
                self._mark_page_done(filename, pg_num)

            pg_num += 1
            self.session_processed_pages += 1
            self._pages_processed_session += 1

            # Show per-page progress every 25 pages
            if pg_num % 25 == 0:
                book_elapsed = time.time() - book_start
                pages_done = pg_num - 1
                pages_remaining = total_pages - pages_done
                if pages_done > 0:
                    rate = pages_done / book_elapsed
                    eta_secs = pages_remaining / rate if rate > 0 else 0
                    book_pct = min(100, int(pages_done / total_pages * 100))
                    console.print(
                        f"  [dim]  Page {pages_done}/{total_pages} ({book_pct}%) | "
                        f"{rate:.1f} pages/s | ETA: {self._format_eta(eta_secs)}[/dim]"
                    )

            if pg_num % 50 == 0:
                self.maybe_take_session_air_break()

        # Save any remaining page progress
        self._save_resume_state()

        book_elapsed = time.time() - book_start
        console.print(
            f"  [green]Done:[/green] {pages_in_book} pages, "
            f"{chunks_in_book} chunks in {self._format_eta(book_elapsed)}"
        )
        if skipped_resume:
            console.print(
                f"  [dim]Skipped {skipped_resume} pages (already indexed)[/dim]"
            )
        logger.info(
            f"Book complete: {filename} — {pages_in_book} new pages, "
            f"{chunks_in_book} new chunks, {skipped_resume} skipped, "
            f"{self._format_eta(book_elapsed)}, errors={errors}"
        )

        result = {
            "filename": filename,
            "pages": pages_in_book,
            "chunks": chunks_in_book,
            "elapsed_seconds": round(book_elapsed, 1),
            "status": "completed",
        }

        # Mark book complete for resume support
        if not self.reindex_mode:
            self._mark_book_complete(filename)

        return result

    def display_stats(self):
        """Display ingestion statistics."""
        table = Table(title="Ingestion Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Pages Processed", str(self.stats["pages_processed"]))
        table.add_row("Chunks Created", str(self.stats["chunks_created"]))
        table.add_row("Chunks Rejected", str(self.stats["chunks_rejected"]))
        table.add_row("Sections Found", str(self.stats["sections_found"]))
        table.add_row("Acts Identified", ", ".join(sorted(self.stats["acts_found"])) if self.stats["acts_found"] else "None")

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

        pdf_files = sorted(f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf"))
        txt_files = sorted(
            f for f in os.listdir(BOOKS_DIR)
            if f.endswith(".txt") and f.replace(".txt", ".pdf") not in pdf_files
        )
        files = pdf_files + txt_files

        if not files:
            console.print(f"[yellow]No PDF or TXT files found in:[/yellow] {BOOKS_DIR}")
            return

        mode_text = (
            "[yellow]RE-INDEX[/yellow]" if self.reindex_mode else "[green]NEW[/green]"
        )
        self._total_books = len(files)
        self._current_book_index = 0
        session_start = time.time()

        console.print(
            f"\n[bold]Enhanced Ingestor[/bold] | Mode: {mode_text} | Books: {len(files)}"
        )

        book_results = []
        for index, filename in enumerate(files):
            file_path = os.path.join(BOOKS_DIR, filename)
            if filename.endswith(".txt"):
                result = self.process_txt_book(filename, file_path)
            else:
                result = self.process_book(filename, file_path)
            book_results.append(result)

            # Show overall progress after each book
            books_done = index + 1
            books_remaining = len(files) - books_done
            elapsed = time.time() - session_start
            if books_done > 0:
                rate = books_done / elapsed
                eta_secs = books_remaining / rate if rate > 0 else 0
                overall_pct = int(books_done / len(files) * 100)
                console.print(
                    f"\n[bold]Overall: {books_done}/{len(files)} books ({overall_pct}%) | "
                    f"Elapsed: {self._format_eta(elapsed)} | "
                    f"ETA: {self._format_eta(eta_secs)}[/bold]"
                )

        # Final stats
        total_elapsed = time.time() - session_start
        console.print("\n[bold green]INGESTION COMPLETE[/bold green]")
        console.print(f"[dim]Total time: {self._format_eta(total_elapsed)}[/dim]")
        self.display_stats()

        # Summary of processed books
        completed = [r for r in book_results if r.get("status") == "completed"]
        skipped = [r for r in book_results if r.get("status") == "skipped"]
        invalid = [r for r in book_results if r.get("status") == "invalid_pdf"]

        console.print(f"\n[bold]Book Summary:[/bold]")
        console.print(f"  [green]Completed:[/green] {len(completed)}")
        console.print(f"  [dim]Skipped (already indexed):[/dim] {len(skipped)}")
        if invalid:
            console.print(f"  [red]Invalid PDFs:[/red] {len(invalid)}")
            for r in invalid:
                console.print(f"    - {r['filename']}: {r.get('error', 'unknown')}")

        console.print(f"\n[bold]Total records in DB:[/bold] {self.collection.count()}")
        logger.info(
            f"Session complete — total records in DB: {self.collection.count()}, "
            f"pages processed: {self.stats['pages_processed']}, "
            f"chunks created: {self.stats['chunks_created']}, "
            f"chunks rejected: {self.stats['chunks_rejected']}"
        )


def create_reindex_tool():
    """Create a utility to re-index existing documents with new metadata."""
    console = Console()

    console.print(
        "\n[bold yellow]Re-Index Mode:[/bold yellow] This will add enhanced metadata"
    )
    console.print("to existing documents without duplicating content.\n")

    confirm = console.input("Continue? (y/n): ")
    if confirm.lower() == "y":
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
