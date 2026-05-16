"""
HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval
Main entry point with CLI support for: init, ingest, status, --help
"""

import os
import sys
import argparse

# Suppress HuggingFace symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def print_error(message: str, details: str = None):
    """Print error with optional details."""
    print(f"[X] {message}")
    if details:
        print(f"  {details}")


def print_success(message: str):
    """Print success message."""
    print(f"[+] {message}")


def print_warning(message: str):
    """Print warning message."""
    print(f"[!] {message}")


def print_info(message: str):
    """Print info message."""
    print(f"[i] {message}")


def get_hector_db_path():
    """Get the Hector database path."""
    return os.path.join(os.path.dirname(__file__), "hector_db")


def get_indexed_documents_count():
    """Get count of indexed documents from ChromaDB."""
    try:
        import chromadb
        from chromadb.config import Settings

        db_path = get_hector_db_path()
        if not os.path.exists(db_path):
            return 0

        client = chromadb.PersistentClient(path=db_path)
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


def get_available_books():
    """Get list of available books in data/Books directory."""
    books_dir = os.path.join(os.path.dirname(__file__), "data", "Books")
    books = []

    if not os.path.exists(books_dir):
        return books

    for file in os.listdir(books_dir):
        if file.lower().endswith('.pdf'):
            file_path = os.path.join(books_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            books.append({
                "name": file,
                "path": file_path,
                "size": size_mb
            })

    return books


def cmd_init(args):
    """Initialize and start HECTOR (Backend + Frontend)."""
    import subprocess
    import time
    import requests

    port = args.port
    frontend_port = args.frontend_port
    no_frontend = args.no_frontend

    print("\n" + "="*60)
    print("H.E.C.T.O.R. INITIALIZATION")
    print("="*60)

    # Start API server
    print("\nStarting API Server...")
    api_process = subprocess.Popen(
        ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        shell=True
    )

    # Wait for API to be ready
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

    # Start Frontend
    frontend_process = None
    if not no_frontend:
        print("\nStarting Frontend Dev Server...")
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

        if not os.path.exists(frontend_dir):
            print_warning("Frontend directory not found")
        else:
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev", "--", "--port", str(frontend_port)],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                shell=True
            )

            # Wait for frontend
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
    print("\n" + "="*60)
    print_success("HECTOR is now running!")
    print(f"• API: http://localhost:{port}")
    if not no_frontend:
        print(f"• Frontend: http://localhost:{frontend_port}")
    print("• Press Ctrl+C to stop all services")
    print("="*60 + "\n")

    # Keep running
    try:
        while True:
            time.sleep(1)
            if api_process.poll() is not None:
                print_error("API server stopped unexpectedly")
                break
            if frontend_process and frontend_process.poll() is not None and not no_frontend:
                print_warning("Frontend server stopped unexpectedly")
    except KeyboardInterrupt:
        print("\nStopping services...")

    # Cleanup
    print("Shutting down services...")
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


def cmd_ingest(args):
    """Ingest books from data/Books directory."""
    print("\n" + "="*60)
    print("H.E.C.T.O.R. INGESTION")
    print("="*60)

    books_dir = os.path.join(os.path.dirname(__file__), "data", "Books")

    if not os.path.exists(books_dir):
        print_error("Books directory not found", books_dir)
        return

    available_books = get_available_books()

    if not available_books:
        print_warning("No books found in data/Books directory")
        return

    print(f"\nFound {len(available_books)} book(s):")
    for book in available_books:
        print(f"  • {book['name']} ({book['size']:.2f} MB)")

    # Try to run ingestor
    try:
        child_env = os.environ.copy()
        child_env.setdefault("PYTHONIOENCODING", "utf-8")
        project_dir = os.path.dirname(__file__)
        ingestor_path = os.path.join(project_dir, "utils", "enhanced_ingestor.py")
        if os.path.exists(ingestor_path):
            print("\nRunning enhanced ingestor...")
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "utils.enhanced_ingestor"],
                cwd=project_dir,
                check=True,
                env=child_env,
            )
        else:
            basic_ingestor = os.path.join(project_dir, "utils", "ingestor.py")
            if os.path.exists(basic_ingestor):
                print("\nRunning basic ingestor...")
                import subprocess
                subprocess.run(
                    [sys.executable, "-m", "utils.ingestor"],
                    cwd=project_dir,
                    check=True,
                    env=child_env,
                )
            else:
                print_error("No ingestor found")
    except Exception as e:
        print_error("Ingestion failed", str(e))


def cmd_status(args):
    """Display HECTOR system status."""
    print("\n" + "="*60)
    print("H.E.C.T.O.R. SYSTEM STATUS")
    print("="*60)

    # Database
    db_path = get_hector_db_path()
    db_exists = os.path.exists(db_path)
    total_docs = get_indexed_documents_count() if db_exists else 0

    print(f"\n[Database]")
    print(f"  Status: {'Connected' if db_exists else 'Not Found'}")
    print(f"  Total Documents: {total_docs}")

    # Books
    books_dir = os.path.join(os.path.dirname(__file__), "data", "Books")
    available_books = get_available_books()

    print(f"\n[Books]")
    print(f"  Available: {len(available_books)}")
    print(f"  Directory: {books_dir}")

    if available_books:
        print(f"\n[Book List]")
        for book in available_books:
            print(f"  • {book['name']} ({book['size']:.2f} MB)")

    # Environment
    print(f"\n[Environment]")
    try:
        import chromadb
        print("  ChromaDB: [+] Installed")
    except ImportError:
        print("  ChromaDB: [X] Not installed")

    try:
        import fastapi
        print("  FastAPI: [+] Installed")
    except ImportError:
        print("  FastAPI: [X] Not installed")

    try:
        import sentence_transformers
        print("  Embeddings: [+] Installed")
    except ImportError:
        print("  Embeddings: [X] Not installed")


def cmd_help(args):
    """Display help message."""
    print("""
HECTOR - Legal Intelligence System

Commands:
  init                   Start HECTOR (API + Frontend)
    --port, -p           API port (default: 8000)
    --frontend-port, -fp Frontend port (default: 3000)
    --no-frontend        Start only backend API

  ingest                 Ingest books from data/Books

  status                 Display system status

  --help, help           Show this help message

  (no command)           Start interactive mode

Examples:
  hector init                    Start the application
  hector init --port 9000        Custom API port
  hector init --no-frontend      API only
  hector ingest                  Ingest new books
  hector status                  Check system status
  hector --help                  Show help
  python main.py                 Interactive mode
""")


def main():
    """Main entry point."""
    # Handle --help before argparse to avoid conflicts
    if "--help" in sys.argv or "-h" in sys.argv:
        cmd_help(None)
        return

    parser = argparse.ArgumentParser(
        description="HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval",
        add_help=False
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Start HECTOR (API + Frontend)")
    init_parser.add_argument("--port", "-p", type=int, default=8000, help="API server port")
    init_parser.add_argument("--frontend-port", "-fp", type=int, default=3000, help="Frontend port")
    init_parser.add_argument("--no-frontend", action="store_true", help="Start only backend API")

    # ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest books from data/Books")
    ingest_parser.add_argument("--force", "-f", action="store_true", help="Re-ingest all books")
    ingest_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed progress")

    # status command
    subparsers.add_parser("status", help="Display system status")

    # help
    subparsers.add_parser("help", help="Show this help message")

    args = parser.parse_args()

    # Handle no command - run interactive mode
    if args.command is None:
        run_interactive()
        return

    # Execute command
    try:
        if args.command == "init":
            cmd_init(args)
        elif args.command == "ingest":
            cmd_ingest(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "help":
            cmd_help(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"[X] Command failed: {args.command}")
        print(f"  {str(e)}")
        sys.exit(1)


def run_interactive():
    """Run HECTOR in interactive CLI mode."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from core.orchestrator import HectorOrchestrator

        console = Console()

        console.clear()
        console.print(Panel.fit(
            "[bold gold1]H.E.C.T.O.R. | LEGAL DECISION ENGINE[/bold gold1]\n"
            "[dim]Status: Operational | Environment: Production (BNS 2023)[/dim]",
            border_style="gold1",
            title="[bold white]v2.1.0[/bold white]"
        ))

        try:
            with console.status("[bold green]Initializing Hector Core...", spinner="dots"):
                hector = HectorOrchestrator()
        except Exception as e:
            print_error("System Failure during Initialization", str(e))
            sys.exit(1)

        console.print("[italic white]Let's get started. [/italic white]\n")

        while True:
            try:
                query = console.input("[bold gold1]User[/bold gold1] [white]> [/white]").strip()

                if not query:
                    continue
                if query.lower() in ["exit", "quit", "done"]:
                    console.print("\n[bold gold1][Hector]:[/bold gold1] Closing the file. We win.")
                    break

                with console.status("[bold blue]Processing Intelligence...", spinner="bouncingBar"):
                    strategy_result = hector.execute(query)

                if strategy_result:
                    content = strategy_result if isinstance(strategy_result, str) else str(strategy_result)

                    if content.strip() == "True":
                        content = "[bold red]System Error:[/bold red] Intelligence layer returned an empty boolean. Re-trying analysis..."

                    console.print(Panel(
                        f"[white]{content}[/white]",
                        title="[bold gold1]Strategy Response[/bold gold1]",
                        border_style="gold1",
                        padding=(1, 2)
                    ))
                else:
                    console.print("[dim red]No data returned from orchestrator.[/dim red]")

            except KeyboardInterrupt:
                console.print("\n[bold red]Interrupted.[/bold red] Session closed.")
                break
            except Exception as e:
                console.print(f"\n[bold red]Runtime Error:[/bold red] {str(e)}")

    except ImportError as e:
        print_error("Missing required dependencies", str(e))
        print_info("Install with: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
