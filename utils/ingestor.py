import os, base64, uuid, requests, json, time, hashlib
import fitz
import chromadb
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
BOOKS_DIR = r"D:\Vs Code\VS code\Hector\data\Books"
DB_PATH = "./hector_db"
OCR_URL = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"

console = Console()

class HectorIngestor:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.embedding_fn = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="indian_law_bns", 
            embedding_function=self.embedding_fn
        )

    def get_page_hash(self, filename, pg_num):
        """Generates a unique digital fingerprint for the page."""
        return hashlib.md5(f"{filename}_{pg_num}".encode()).hexdigest()

    def cooldown_timer(self, minutes=15):
        """Displays a high-visibility countdown clock."""
        seconds = minutes * 60
        with Live(auto_refresh=True, console=console) as live:
            while seconds > 0:
                mins, secs = divmod(seconds, 60)
                timer_text = Text(f"{mins:02d}:{secs:02d}", style="bold yellow", justify="center")
                live.update(Panel(timer_text, title="[bold red]Cooldown in Progress[/bold red]", subtitle="Resting API Connection"))
                time.sleep(1)
                seconds -= 1
        console.print("[bold green]✓ Cooldown Complete. Resuming Ingestion...[/bold green]")

    def process_with_heartbeat(self):
        files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf")]
        
        try:
            for index, filename in enumerate(files):
                file_path = os.path.join(BOOKS_DIR, filename)
                doc = fitz.open(file_path)
                console.print(f"\n[bold magenta]BOOK {index+1}/{len(files)}[/bold magenta] | [bold cyan]{filename}[/bold cyan] ({len(doc)} pages)")

                for pg_num in range(len(doc)):
                    page_hash = self.get_page_hash(filename, pg_num)
                    
                    # 1. Duplicate Verification Check
                    existing = self.collection.get(where={"page_hash": page_hash})
                    if len(existing['ids']) > 0:
                        continue

                    # 2. Page Extraction & High-Res Rendering
                    page = doc.load_page(pg_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    b64_img = base64.b64encode(pix.tobytes("png")).decode("utf-8")
                    
                    # 3. Call NVIDIA Deep OCR
                    headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Accept": "application/json"}
                    payload = {"input": [{"type": "image_url", "url": f"data:image/png;base64,{b64_img}"}]}
                    
                    try:
                        response = requests.post(OCR_URL, headers=headers, json=payload, timeout=60)
                        if response.status_code == 200:
                            ocr_data = response.json().get("data", [])
                            text = " ".join([d.get("text", "") for d in ocr_data])
                            
                            # 4. Detailed Mapping Metadata
                            self.collection.add(
                                documents=[text],
                                metadatas=[{
                                    "source": filename,
                                    "page": pg_num + 1,
                                    "page_hash": page_hash,
                                    "ingested_at": str(datetime.now()),
                                    "mapping_accuracy": "detailed_scan_v3"
                                }],
                                ids=[str(uuid.uuid4())]
                            )
                            console.print(f"  [green]✓[/green] Ingested Page {pg_num + 1}")
                        else:
                            console.print(f"  [red]×[/red] Error Page {pg_num + 1} | HTTP {response.status_code}")
                    except Exception as e:
                        console.print(f"  [bold red]![/bold red] Connection Error Page {pg_num + 1}: {e}")
                        time.sleep(5) # Small pause to recover connection
                
                doc.close()
                
                # 5. Inter-book Cooldown
                if index < len(files) - 1:
                    console.print(f"\n[bold yellow]Book {index+1} Complete.[/bold yellow] Triggering safety cooldown...")
                    self.cooldown_timer(minutes=15)
                
        except KeyboardInterrupt:
            console.print("\n[bold red]STOP SIGNAL RECEIVED.[/bold red] Flushing buffers...")
        finally:
            self.client.heartbeat() # Ensure DB sync
            console.print(f"\n[bold green]INGESTION SUMMARY[/bold green]")
            console.print(f"Total Unique Records in DB: [cyan]{self.collection.count()}[/cyan]")
            console.print("[dim]Data persisted safely to hector_db[/dim]")

if __name__ == "__main__":
    HectorIngestor().process_with_heartbeat()