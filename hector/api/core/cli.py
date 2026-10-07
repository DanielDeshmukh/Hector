"""
HECTOR CLI - Command Line Interface for HECTOR Legal Intelligence System.
Provides commands: init, ingest, status, --help
"""

from __future__ import annotations
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional
import logging

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    typer = None
    Console = None

# Initialize console
console = Console() if Console else None

# Suppress HuggingFace warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# App instance
app = typer.Typer(
    help="HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval"
)


def get_books_directory() -> Path:
    """Get the Books directory path."""
    return Path(__file__).parent.parent / "data" / "Books"


def get_hector_db_path() -> Path:
    """Get the Hector database path."""
    return Path(__file__).parent.parent / "hector_db"


def print_success(message: str):
    """Print success message."""
    if console:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        print(f"✓ {message}")


def print_error(message: str, details: Optional[str] = None):
    """Print error message with optional details."""
    if console:
        console.print(f"[bold red]✗[/bold red] {message}")
        if details:
            console.print(f"  [dim]{details}[/dim]")
    else:
        print(f"✗ {message}")
        if details:
            print(f"  {details}")


def print_warning(message: str):
    """Print warning message."""
    if console:
        console.print(f"[bold yellow]![/bold yellow] {message}")
    else:
        print(f"! {message}")


def print_info(message: str):
    """Print info message."""
    if console:
        console.print(f"[bold cyan]ℹ[/bold cyan] {message}")
    else:
        print(f"ℹ {message}")


def get_indexed_documents_count() -> int:
    """Get count of indexed documents from ChromaDB."""
    try:
        import chromadb

        db_path = get_hector_db_path()
        if not db_path.exists():
            return 0

        client = chromadb.PersistentClient(path=str(db_path))
        collections = client.list_collections()

        total_count = 0
        for coll in collections:
            try:
                total_count += coll.count()
            except Exception:
                logging.debug("Failed to get collection count for %s", coll)

        return total_count
    except Exception as e:
        print_warning(f"Could not connect to database: {e}")
        return 0


def get_available_books() -> list[dict]:
    """Get list of available books in data/Books directory."""
    books_dir = get_books_directory()
    books = []

    if not books_dir.exists():
        return books

    for file in books_dir.iterdir():
        if file.is_file() and file.suffix.lower() in [".pdf", ".txt"]:
            books.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size / (1024 * 1024),  # MB
                }
            )

    return books


def get_indexed_books() -> list[str]:
    """Get list of books already indexed in the database."""
    try:
        import chromadb

        db_path = get_hector_db_path()
        if not db_path.exists():
            return []

        client = chromadb.PersistentClient(path=str(db_path))
        collections = client.list_collections()

        indexed = set()
        for coll in collections:
            try:
                # Get sample to extract source info
                results = coll.get(limit=min(100, coll.count()))
                if results and results.get("metadatas"):
                    for meta in results["metadatas"]:
                        if meta and meta.get("source"):
                            indexed.add(meta["source"])
            except Exception:
                logging.debug("Failed to get source metadata from collection %s", coll)

        return list(indexed)
    except Exception:
        return []


def _pump_log(stream, prefix: str):
    try:
        while True:
            raw = stream.readline()
            if not raw:
                break
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            sys.stdout.write(f"{prefix}{raw}")
            sys.stdout.flush()
    except Exception:
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        import httpx

        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        return resp.status_code in (200, 304)
    except Exception:
        return False


def _wait_http(url: str, attempts: int, timeout: float = 5.0) -> bool:
    for _ in range(attempts):
        if _http_ok(url, timeout=timeout):
            return True
        time.sleep(1)
    return False


def _stop_process(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
            )
        else:
            try:
                process.kill()
            except Exception:
                pass


def _run_services(
    port: int,
    frontend_port: int,
    no_frontend: bool,
    reload: bool,
    open_ui: bool,
    title: str,
):
    if not typer:
        print_error("Typer not installed. Run: pip install typer rich")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold gold1]{title}[/bold gold1]\n"
            "[dim]Starting Backend and Frontend services...[/dim]",
            border_style="gold1",
            padding=(1, 2),
        )
    )

    import threading

    hector_dir = Path(__file__).resolve().parents[2]
    api_dir = Path(__file__).resolve().parents[1]
    api_process = None
    frontend_process = None

    try:
        api_url = f"http://127.0.0.1:{port}/healthz"
        if _http_ok(api_url):
            print_success(f"API Server already running on http://localhost:{port}")
        else:
            console.print("\n[bold cyan]Starting API Server...[/bold cyan]")
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "api.app:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ]
            if reload:
                cmd.append("--reload")
            api_process = subprocess.Popen(
                cmd,
                cwd=str(api_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32"
                else 0,
            )
            threading.Thread(
                target=_pump_log, args=(api_process.stdout, "[api] "), daemon=True
            ).start()
            threading.Thread(
                target=_pump_log, args=(api_process.stderr, "[api:err] "), daemon=True
            ).start()
            if _wait_http(api_url, attempts=90, timeout=5.0):
                print_success(f"API Server running on http://localhost:{port}")
            else:
                print_warning("API server might not be ready yet (see [api] logs)")

        if not no_frontend:
            if not (hector_dir / "package.json").is_file():
                print_warning(f"Frontend not found (no package.json in {hector_dir})")
            elif _http_ok(f"http://127.0.0.1:{frontend_port}", timeout=2.0):
                print_success(
                    f"Frontend already running on http://localhost:{frontend_port}"
                )
            else:
                console.print("\n[bold cyan]Starting Frontend Dev Server...[/bold cyan]")
                env = os.environ.copy()
                env["PORT"] = str(frontend_port)
                env["NEXT_PUBLIC_HECTOR_API_URL"] = f"http://localhost:{port}"
                env["NODE_OPTIONS"] = "--max-old-space-size=4096"
                frontend_process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(hector_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32"
                    else 0,
                    shell=True,
                )
                threading.Thread(
                    target=_pump_log,
                    args=(frontend_process.stdout, "[web] "),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=_pump_log,
                    args=(frontend_process.stderr, "[web:err] "),
                    daemon=True,
                ).start()
                if _wait_http(
                    f"http://127.0.0.1:{frontend_port}", attempts=120, timeout=30.0
                ):
                    print_success(
                        f"Frontend running on http://localhost:{frontend_port}"
                    )
                else:
                    print_warning(
                        "Frontend might not be ready yet (see [web] logs)"
                    )

        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold green]HECTOR is now running![/bold green]\n\n"
                f"• API: [cyan]http://localhost:{port}[/cyan]\n"
                f"{'' if no_frontend else f'• Frontend: [cyan]http://localhost:{frontend_port}[/cyan]\n'}"
                f"\n[dim]Press Ctrl+C to stop all services[/dim]",
                border_style="green",
                padding=(1, 2),
            )
        )

        if open_ui and not no_frontend:
            import webbrowser

            webbrowser.open(f"http://localhost:{frontend_port}")

        console.print("\n[dim]Services are running. Press Ctrl+C to stop...[/dim]")
        try:
            while True:
                time.sleep(1)
                if api_process and api_process.poll() is not None:
                    print_error("API server stopped unexpectedly")
                    break
                if (
                    frontend_process
                    and frontend_process.poll() is not None
                    and not no_frontend
                ):
                    print_warning("Frontend server stopped unexpectedly")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping services...[/yellow]")

    except FileNotFoundError as e:
        print_error("Required command not found", str(e))
        print_info("Make sure Node.js and npm are installed for frontend")
    except Exception as e:
        print_error("Failed to start services", str(e))
    finally:
        console.print("\n[dim]Shutting down services...[/dim]")
        _stop_process(frontend_process)
        _stop_process(api_process)
        print_success("All services stopped")


@app.command()
def init(
    port: int = typer.Option(8000, "--port", "-p", help="API server port"),
    frontend_port: int = typer.Option(
        3000, "--frontend-port", "-fp", help="Frontend dev server port"
    ),
    no_frontend: bool = typer.Option(
        False, "--no-frontend", help="Start only the backend API"
    ),
):
    """
    Initialize and start HECTOR (Backend API + Frontend).
    """
    _run_services(
        port,
        frontend_port,
        no_frontend,
        reload=True,
        open_ui=False,
        title="H.E.C.T.O.R. INITIALIZATION",
    )


@app.command()
def run(
    port: int = typer.Option(8000, "--port", "-p", help="API server port"),
    frontend_port: int = typer.Option(
        3000, "--frontend-port", "-fp", help="Frontend dev server port"
    ),
    no_frontend: bool = typer.Option(
        False, "--no-frontend", help="Start only the backend API"
    ),
    open_ui: bool = typer.Option(False, "--open", help="Open the UI in a browser"),
):
    """
    Start HECTOR for the demo (Backend API + Frontend) with one command.
    """
    _run_services(
        port,
        frontend_port,
        no_frontend,
        reload=False,
        open_ui=open_ui,
        title="H.E.C.T.O.R. RUN",
    )


@app.command()
def ingest(
    force: bool = typer.Option(
        False, "--force", "-f", help="Re-ingest all books even if already indexed"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress"
    ),
):
    """
    Ingest books from data/Books directory into HECTOR database.
    """
    if not typer:
        print_error("Typer not installed. Run: pip install typer rich")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold gold1]HECTOR INGESTION[/bold gold1]\n"
            "[dim]Processing legal documents...[/dim]",
            border_style="gold1",
            padding=(1, 2),
        )
    )

    books_dir = get_books_directory()

    # Check if books directory exists
    if not books_dir.exists():
        print_error("Books directory not found", str(books_dir))
        raise typer.Exit(1)

    # Get available books
    available_books = get_available_books()

    if not available_books:
        print_warning("No books found in data/Books directory")
        return

    # Get indexed books
    indexed_books = get_indexed_books() if not force else []

    # Filter books to ingest
    books_to_ingest = []
    for book in available_books:
        if book["name"] not in indexed_books:
            books_to_ingest.append(book)

    if not books_to_ingest:
        print_success(f"All {len(available_books)} books are already indexed")
        return

    console.print(
        f"\n[bold]Found {len(books_to_ingest)} new book(s) to ingest:[/bold]\n"
    )

    for book in books_to_ingest:
        console.print(f"  • {book['name']} ({book['size']:.2f} MB)")

    console.print()

    # Import ingestor
    try:
        # Check for enhanced ingestor first
        ingestor_path = Path(__file__).parent.parent / "utils" / "enhanced_ingestor.py"
        if ingestor_path.exists():
            # Use enhanced ingestor
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.enhanced_ingestor import Ingestor

            ingestor = Ingestor()
        else:
            # Fallback to basic ingestor
            basic_ingestor_path = Path(__file__).parent.parent / "utils" / "ingestor.py"
            if basic_ingestor_path.exists():
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from utils.ingestor import Ingestor

                ingestor = Ingestor()
            else:
                print_error("Ingestor module not found")
                raise typer.Exit(1)
    except Exception as e:
        print_error("Failed to import ingestor", str(e))
        raise typer.Exit(1)

    # Ingest each book
    success_count = 0
    error_count = 0

    for book in books_to_ingest:
        try:
            console.print(f"\n[cyan]Ingesting:[/cyan] {book['name']}")
            with console.status(
                f"[bold green]Processing {book['name']}...", spinner="dots"
            ):
                result = ingestor.ingest(book["path"])
                if result:
                    print_success(f"Ingested: {book['name']}")
                    success_count += 1
                else:
                    print_warning(f"Skipped: {book['name']} (no content extracted)")
        except Exception as e:
            print_error(f"Failed to ingest {book['name']}", str(e))
            error_count += 1

    # Summary
    console.print("\n")
    if success_count > 0:
        print_success(f"Successfully ingested {success_count} book(s)")
    if error_count > 0:
        print_error(f"Failed to ingest {error_count} book(s)")

    # Show updated status
    total_docs = get_indexed_documents_count()
    console.print(f"\n[bold]Total documents in database:[/bold] {total_docs}")


@app.command()
def status():
    """
    Display HECTOR system status and statistics.
    """
    if not typer:
        print_error("Typer not installed. Run: pip install typer rich")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold gold1]HECTOR SYSTEM STATUS[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )

    # Database status
    db_path = get_hector_db_path()
    db_exists = db_path.exists()

    # Get statistics
    total_docs = get_indexed_documents_count() if db_exists else 0

    # Create status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan", width=25)
    table.add_column("Value", style="white")

    table.add_row(
        "Database", "[green]Connected[/green]" if db_exists else "[red]Not Found[/red]"
    )
    table.add_row("Total Documents", str(total_docs))

    # Books directory
    books_dir = get_books_directory()
    available_books = get_available_books()
    table.add_row("Available Books", str(len(available_books)))
    table.add_row("Books Directory", str(books_dir))

    # Indexed vs not indexed
    if not db_exists:
        indexed_books = []
    else:
        indexed_books = get_indexed_books()

    not_indexed = len(available_books) - len(
        [b for b in available_books if b["name"] in indexed_books]
    )
    table.add_row("Indexed Books", str(len(indexed_books)))
    table.add_row("Pending Ingestion", str(not_indexed))

    console.print(table)

    # Show available books
    if available_books:
        console.print("\n[bold]Available Books:[/bold]")
        books_table = Table(show_header=True, header_style="bold magenta")
        books_table.add_column("Name", style="white")
        books_table.add_column("Size (MB)", style="dim", justify="right")
        books_table.add_column("Status", style="dim")

        for book in available_books:
            status_str = (
                "[green]Indexed[/green]"
                if book["name"] in indexed_books
                else "[yellow]Pending[/yellow]"
            )
            books_table.add_row(book["name"], f"{book['size']:.2f}", status_str)

        console.print(books_table)

    # Environment check
    console.print("\n[bold]Environment:[/bold]")
    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column("Component", style="bold cyan", width=20)
    env_table.add_column("Status", style="white")

    # Check Python packages
    try:
        import chromadb  # noqa: F401

        env_table.add_row("ChromaDB", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("ChromaDB", "[red]✗ Not installed[/red]")

    try:
        import fastapi  # noqa: F401

        env_table.add_row("FastAPI", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("FastAPI", "[red]✗ Not installed[/red]")

    try:
        import sentence_transformers  # noqa: F401

        env_table.add_row("Embeddings", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("Embeddings", "[red]✗ Not installed[/red]")

    console.print(env_table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Legal query to search"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(5, "--size", "-s", help="Results per page"),
    format: str = typer.Option(
        "summary", "--format", "-f", help="Output format: summary, detailed, citations"
    ),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Run verification"),
):
    """Search the legal corpus for a query."""
    import httpx

    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/search",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={
                    "query": query,
                    "page": page,
                    "page_size": page_size,
                    "verify": verify,
                    "format": format,
                    "include_related": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        if console:
            console.print(
                Panel.fit(
                    f"[bold cyan]Search Results[/bold cyan]\nQuery: {query}\nRoute: {data.get('route', 'N/A')}\nConfidence: {data.get('answer_confidence', 0)}%",
                    border_style="cyan",
                )
            )
            table = Table(title="Results")
            table.add_column("#", style="dim")
            table.add_column("Act", style="bold")
            table.add_column("Snippet")
            table.add_column("Score", style="green")
            for i, item in enumerate(data.get("items", []), 1):
                table.add_row(
                    str(i),
                    item.get("act", "?"),
                    (item.get("snippet", "")[:80] + "...")
                    if len(item.get("snippet", "")) > 80
                    else item.get("snippet", ""),
                    f"{item.get('similarity_score', 0):.2f}",
                )
            console.print(table)
        else:
            print(f"Query: {query}")
            print(f"Route: {data.get('route', 'N/A')}")
            print(f"Confidence: {data.get('answer_confidence', 0)}%")
            for i, item in enumerate(data.get("items", []), 1):
                print(
                    f"  {i}. [{item.get('act', '?')}] {item.get('snippet', '')[:100]}... (score: {item.get('similarity_score', 0):.2f})"
                )
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        raise typer.Exit(1)


@app.command()
def compare(
    section: str = typer.Argument(..., help="Section number to compare"),
    act: str = typer.Option("IPC", "--act", "-a", help="Act: IPC or BNS"),
    page_size: int = typer.Option(3, "--size", "-s", help="Results per side"),
):
    """Compare a section between IPC and BNS."""
    import httpx

    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/compare",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={"section": section, "act": act, "page_size": page_size},
            )
            resp.raise_for_status()
            data = resp.json()

        counterpart_act = "BNS" if act.upper() == "IPC" else "IPC"
        if console:
            console.print(
                Panel.fit(
                    f"[bold cyan]IPC ↔ BNS Comparison[/bold cyan]\nRequested: {act} Section {data.get('requested_section', section)}\nCounterpart: {counterpart_act} Section {data.get('counterpart_section', '?')}\nNote: {data.get('note', 'N/A')}",
                    border_style="cyan",
                )
            )
            for label, items in [
                ("Requested", data.get("requested_results", [])),
                ("Counterpart", data.get("counterpart_results", [])),
            ]:
                table = Table(
                    title=f"{label} ({act if label == 'Requested' else counterpart_act})"
                )
                table.add_column("#", style="dim")
                table.add_column("Score", style="green")
                table.add_column("Snippet")
                for i, item in enumerate(items, 1):
                    table.add_row(
                        str(i),
                        f"{item.get('similarity_score', 0):.2f}",
                        (item.get("snippet", "")[:80] + "...")
                        if len(item.get("snippet", "")) > 80
                        else item.get("snippet", ""),
                    )
                console.print(table)
        else:
            print(f"Requested: {act} Section {data.get('requested_section', section)}")
            print(
                f"Counterpart: {counterpart_act} Section {data.get('counterpart_section', '?')}"
            )
            print(f"Note: {data.get('note', 'N/A')}")
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        raise typer.Exit(1)


@app.command()
def deep_cite(
    query: str = typer.Argument(..., help="Legal query for deep citation analysis"),
):
    """Run deep citation verification on a legal query."""
    import httpx

    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/search",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={
                    "query": query,
                    "page": 1,
                    "page_size": 10,
                    "verify": True,
                    "format": "citations",
                    "include_related": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        if console:
            console.print(
                Panel.fit(
                    f"[bold cyan]Deep Citation Analysis[/bold cyan]\nQuery: {query}\nRoute: {data.get('route', 'N/A')}\nConfidence: {data.get('answer_confidence', 0)}%",
                    border_style="cyan",
                )
            )
            sources = data.get("source_sections", [])
            if sources:
                table = Table(title="Cited Sources")
                table.add_column("#", style="dim")
                table.add_column("Section", style="bold")
                table.add_column("Relevance", style="green")
                table.add_column("Text")
                for i, src in enumerate(sources, 1):
                    table.add_row(
                        str(i),
                        f"{src.get('section', '?')} {src.get('act', '')}",
                        f"{src.get('similarity', 0):.1%}",
                        (src.get("text", "")[:60] + "...")
                        if len(src.get("text", "")) > 60
                        else src.get("text", ""),
                    )
                console.print(table)
            else:
                console.print("[yellow]No sources found[/yellow]")
        else:
            print(f"Query: {query}")
            print(f"Confidence: {data.get('answer_confidence', 0)}%")
            for i, src in enumerate(data.get("source_sections", []), 1):
                print(
                    f"  {i}. {src.get('section', '?')} {src.get('act', '')} ({src.get('similarity', 0):.1%})"
                )
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        raise typer.Exit(1)


@app.command()
def help():
    """
    Display HECTOR command help and usage guide.
    """
    if not typer:
        print("HECTOR CLI Help:")
        print("  hector run      - Start HECTOR (backend + frontend)")
        print("  hector init     - Start HECTOR in dev mode (with auto-reload)")
        print("  hector ingest   - Ingest books from data/Books")
        print("  hector status  - Show system status")
        print("  hector --help   - Show this help")
        return

    console.print(
        Panel.fit(
            """
[bold gold1]HECTOR - LEGAL INTELLIGENCE SYSTEM[/bold gold1]

[bold cyan]Commands:[/bold cyan]

  [bold]run[/bold]               Start HECTOR (API + Frontend) for the demo
    --port, -p           API server port (default: 8000)
    --frontend-port, -fp Frontend port (default: 3000)
    --no-frontend        Start only backend API
    --open               Open the UI in a browser

  [bold]init[/bold]               Start HECTOR (API + Frontend) with auto-reload
    --port, -p           API server port (default: 8000)
    --frontend-port, -fp Frontend port (default: 3000)
    --no-frontend        Start only backend API

  [bold]ingest[/bold]            Ingest books from data/Books
    --force, -f          Re-ingest all books
    --verbose, -v        Show detailed progress

  [bold]search[/bold]            Search the legal corpus
    --page, -p           Page number (default: 1)
    --size, -s           Results per page (default: 5)
    --format, -f         Output format: summary, detailed, citations
    --verify/--no-verify Run verification

  [bold]compare[/bold]           Compare IPC ↔ BNS sections
    --act, -a            Act: IPC or BNS (default: IPC)
    --size, -s           Results per side (default: 3)

  [bold]deep-cite[/bold]         Deep citation verification

  [bold]status[/bold]            Display system status and statistics

  [bold]--help, help[/bold]      Show this help message

[bold cyan]Examples:[/bold cyan]

  hector run                     # Start both API and frontend
  hector run --open              # Start and open the browser
  hector run --port 9000         # Custom API port
  hector run --no-frontend       # API only
  hector init                    # Start in dev mode (auto-reload)
  hector ingest                 # Ingest new books
  hector ingest --force         # Re-ingest all books
  hector search "IPC Section 302" # Search for legal provisions
  hector compare 302 --act IPC  # Compare IPC 302 with BNS equivalent
  hector deep-cite "murder punishment" # Deep citation analysis
  hector status                 # Check system status

[bold cyan]Quick Start:[/bold cyan]

  1. hector run                 # Start the application
  2. Open http://localhost:3000  # Access the UI
  3. hector ingest              # Add your legal books

[dim]HECTOR v2.1.0 | Hard-RAG Legal Intelligence[/dim]
        """,
            border_style="gold1",
            padding=(1, 2),
        )
    )


# Entry point for hector command
def main():
    """Main entry point for hector CLI."""
    if not typer:
        print("Error: typer and rich are required.")
        print("Install with: pip install typer rich")
        sys.exit(1)

    # Handle --help as first argument
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "help"]:
        help()
        return

    app()


if __name__ == "__main__":
    main()
