"""
HECTOR CLI - Command Line Interface for HECTOR Legal Intelligence System.
Provides commands: init, ingest, status, --help
"""

from __future__ import annotations
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
except ImportError:
    typer = None
    Console = None

# Initialize console
console = Console() if Console else None

# Suppress HuggingFace warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# App instance
app = typer.Typer(help="HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval")


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
        from chromadb.config import Settings

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
                pass

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
        if file.is_file() and file.suffix.lower() in ['.pdf', '.txt']:
            books.append({
                "name": file.name,
                "path": str(file),
                "size": file.stat().st_size / (1024 * 1024)  # MB
            })

    return books


def get_indexed_books() -> list[str]:
    """Get list of books already indexed in the database."""
    try:
        import chromadb
        from chromadb.config import Settings

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
                if results and results.get('metadatas'):
                    for meta in results['metadatas']:
                        if meta and meta.get('source'):
                            indexed.add(meta['source'])
            except Exception:
                pass

        return list(indexed)
    except Exception:
        return []


@app.command()
def init(
    port: int = typer.Option(8000, "--port", "-p", help="API server port"),
    frontend_port: int = typer.Option(3000, "--frontend-port", "-fp", help="Frontend dev server port"),
    no_frontend: bool = typer.Option(False, "--no-frontend", help="Start only the backend API"),
):
    """
    Initialize and start HECTOR (Backend API + Frontend).
    """
    if not typer:
        print_error("Typer not installed. Run: pip install typer rich")
        raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold gold1]H.E.C.T.O.R. INITIALIZATION[/bold gold1]\n"
        "[dim]Starting Backend and Frontend services...[/dim]",
        border_style="gold1",
        padding=(1, 2)
    ))

    # Start API server in background
    api_process = None
    frontend_process = None

    try:
        # Start FastAPI backend
        console.print("\n[bold cyan]Starting API Server...[/bold cyan]")
        api_process = subprocess.Popen(
            ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )

        # Wait for API to be ready
        import requests
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port}/status", timeout=1)
                if response.status_code == 200:
                    print_success(f"API Server running on http://localhost:{port}")
                    break
            except Exception:
                pass
            time.sleep(1)
            if i == max_retries - 1:
                print_warning("API server might not be ready yet")

        # Start Frontend (unless disabled)
        if not no_frontend:
            console.print("\n[bold cyan]Starting Frontend Dev Server...[/bold cyan]")
            frontend_dir = Path(__file__).parent.parent / "frontend"

            # Check if frontend exists
            if not frontend_dir.exists():
                print_warning("Frontend directory not found")
            else:
                frontend_process = subprocess.Popen(
                    ["npm", "run", "dev", "--", "--port", str(frontend_port)],
                    cwd=str(frontend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                    shell=True
                )

                # Wait for frontend to be ready
                for i in range(30):
                    try:
                        response = requests.get(f"http://localhost:{frontend_port}", timeout=1)
                        if response.status_code in [200, 304]:
                            print_success(f"Frontend running on http://localhost:{frontend_port}")
                            break
                    except Exception:
                        pass
                    time.sleep(1)
                    if i == 29:
                        print_warning("Frontend server might not be ready yet")

        # Print final status
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]HECTOR is now running![/bold green]\n\n"
            f"• API: [cyan]http://localhost:{port}[/cyan]\n"
            f"{'' if no_frontend else f'• Frontend: [cyan]http://localhost:{frontend_port}[/cyan]\n'}"
            f"\n[dim]Press Ctrl+C to stop all services[/dim]",
            border_style="green",
            padding=(1, 2)
        ))

        # Keep running
        console.print("\n[dim]Services are running. Press Ctrl+C to stop...[/dim]")
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                if api_process and api_process.poll() is not None:
                    print_error("API server stopped unexpectedly")
                    break
                if frontend_process and frontend_process.poll() is not None and not no_frontend:
                    print_warning("Frontend server stopped unexpectedly")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping services...[/yellow]")

    except FileNotFoundError as e:
        print_error("Required command not found", str(e))
        print_info("Make sure Node.js and npm are installed for frontend")
    except Exception as e:
        print_error("Failed to start services", str(e))
    finally:
        # Cleanup
        console.print("\n[dim]Shutting down services...[/dim]")
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        print_success("All services stopped")


@app.command()
def ingest(
    force: bool = typer.Option(False, "--force", "-f", help="Re-ingest all books even if already indexed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
):
    """
    Ingest books from data/Books directory into HECTOR database.
    """
    if not typer:
        print_error("Typer not installed. Run: pip install typer rich")
        raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold gold1]HECTOR INGESTION[/bold gold1]\n"
        "[dim]Processing legal documents...[/dim]",
        border_style="gold1",
        padding=(1, 2)
    ))

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
        if book['name'] not in indexed_books:
            books_to_ingest.append(book)

    if not books_to_ingest:
        print_success(f"All {len(available_books)} books are already indexed")
        return

    console.print(f"\n[bold]Found {len(books_to_ingest)} new book(s) to ingest:[/bold]\n")

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
            with console.status(f"[bold green]Processing {book['name']}...", spinner="dots"):
                result = ingestor.ingest(book['path'])
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

    console.print(Panel.fit(
        "[bold gold1]HECTOR SYSTEM STATUS[/bold gold1]",
        border_style="gold1",
        padding=(1, 2)
    ))

    # Database status
    db_path = get_hector_db_path()
    db_exists = db_path.exists()

    # Get statistics
    total_docs = get_indexed_documents_count() if db_exists else 0

    # Create status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan", width=25)
    table.add_column("Value", style="white")

    table.add_row("Database", "[green]Connected[/green]" if db_exists else "[red]Not Found[/red]")
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

    not_indexed = len(available_books) - len([b for b in available_books if b['name'] in indexed_books])
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
            status_str = "[green]Indexed[/green]" if book['name'] in indexed_books else "[yellow]Pending[/yellow]"
            books_table.add_row(book['name'], f"{book['size']:.2f}", status_str)

        console.print(books_table)

    # Environment check
    console.print("\n[bold]Environment:[/bold]")
    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column("Component", style="bold cyan", width=20)
    env_table.add_column("Status", style="white")

    # Check Python packages
    try:
        import chromadb
        env_table.add_row("ChromaDB", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("ChromaDB", "[red]✗ Not installed[/red]")

    try:
        import fastapi
        env_table.add_row("FastAPI", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("FastAPI", "[red]✗ Not installed[/red]")

    try:
        import sentence_transformers
        env_table.add_row("Embeddings", "[green]✓ Installed[/green]")
    except ImportError:
        env_table.add_row("Embeddings", "[red]✗ Not installed[/red]")

    console.print(env_table)


@app.command()
def help():
    """
    Display HECTOR command help and usage guide.
    """
    if not typer:
        print("HECTOR CLI Help:")
        print("  hector init     - Start HECTOR (backend + frontend)")
        print("  hector ingest   - Ingest books from data/Books")
        print("  hector status  - Show system status")
        print("  hector --help   - Show this help")
        return

    console.print(Panel.fit(
        """
[bold gold1]HECTOR - LEGAL INTELLIGENCE SYSTEM[/bold gold1]

[bold cyan]Commands:[/bold cyan]

  [bold]init[/bold]               Start HECTOR (API + Frontend)
    --port, -p           API server port (default: 8000)
    --frontend-port, -fp Frontend port (default: 3000)
    --no-frontend        Start only backend API

  [bold]ingest[/bold]            Ingest books from data/Books
    --force, -f          Re-ingest all books
    --verbose, -v        Show detailed progress

  [bold]status[/bold]            Display system status and statistics

  [bold]--help, help[/bold]      Show this help message

[bold cyan]Examples:[/bold cyan]

  hector init                    # Start both API and frontend
  hector init --port 9000        # Custom API port
  hector init --no-frontend      # API only
  hector ingest                 # Ingest new books
  hector ingest --force         # Re-ingest all books
  hector status                 # Check system status

[bold cyan]Quick Start:[/bold cyan]

  1. hector init                # Start the application
  2. Open http://localhost:3000  # Access the UI
  3. hector ingest              # Add your legal books

[dim]HECTOR v2.1.0 | Hard-RAG Legal Intelligence[/dim]
        """,
        border_style="gold1",
        padding=(1, 2)
    ))


# Entry point for hector command
def main():
    """Main entry point for hector CLI."""
    if not typer:
        print("Error: typer and rich are required.")
        print("Install with: pip install typer rich")
        sys.exit(1)

    # Handle --help as first argument
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', 'help']:
        help()
        return

    app()


if __name__ == "__main__":
    main()