"""
HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval
Main entry point with CLI support for: init, ingest, status, --help
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import atexit
import logging
from pathlib import Path

# Suppress HuggingFace symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Process tracking file
PROCESS_FILE = os.path.join(os.path.dirname(__file__), ".hector_processes.json")


def save_process_info(port: int, frontend_port: int = None, pid: int = None):
    """Save process information to file."""
    try:
        data = {}
        if os.path.exists(PROCESS_FILE):
            with open(PROCESS_FILE, 'r') as f:
                data = json.load(f)
        
        data['last_api_port'] = port
        if frontend_port:
            data['last_frontend_port'] = frontend_port
        if pid:
            data['pids'] = data.get('pids', [])
            if pid not in data['pids']:
                data['pids'].append(pid)
        
        with open(PROCESS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logging.debug("Failed to save process info: %s", e)


def load_process_info():
    """Load process information from file."""
    try:
        if os.path.exists(PROCESS_FILE):
            with open(PROCESS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.debug("Failed to load process info: %s", e)
    return {}


def clear_process_info():
    """Clear process information file."""
    try:
        if os.path.exists(PROCESS_FILE):
            os.remove(PROCESS_FILE)
    except Exception as e:
        logging.debug("Failed to clear process info: %s", e)


def get_processes_on_ports(ports: list) -> list:
    """Get PIDs of processes using specified ports."""
    pids = []
    try:
        if sys.platform == "win32":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
            for line in result.stdout.split("\n"):
                for port in ports:
                    if f":{port} " in line and "LISTENING" in line:
                        parts = line.split()
                        pid = int(parts[-1])
                        if pid not in pids:
                            pids.append(pid)
        else:
            for port in ports:
                result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
                for line in result.stdout.split("\n")[1:]:
                    if line.strip():
                        parts = line.split()
                        try:
                            pid = int(parts[1])
                            if pid not in pids:
                                pids.append(pid)
                        except (ValueError, IndexError) as e:
                            logging.debug("Failed to parse PID from lsof output: %s", e)
    except Exception as e:
        logging.debug("Failed to get processes on ports: %s", e)
    return pids


def cleanup_stuck_ports(ports: list):
    """Clean up any stuck processes on the given ports."""
    pids = get_processes_on_ports(ports)
    for pid in pids:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, capture_output=True)
            else:
                subprocess.run(["kill", "-9", str(pid)], check=True)
            print_success(f"Cleaned up stuck process (PID: {pid})")
        except Exception as e:
            logging.debug("Failed to kill stuck process %d: %s", pid, e)


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


def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            s.close()
        return True
    except OSError:
        return False


def find_available_port(start_port: int = 3000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None


def kill_process_on_port(port: int) -> bool:
    """Kill the process using the specified port (Windows and Unix)."""
    try:
        if sys.platform == "win32":
            # Windows: use netstat and taskkill
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split("\n"):
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    try:
                        subprocess.run(["taskkill", "/PID", pid, "/F"], check=True, capture_output=True)
                        print_success(f"Killed process on port {port} (PID: {pid})")
                        return True
                    except subprocess.CalledProcessError as e:
                        logging.debug("Failed to kill process %s on port %d: %s", pid, port, e)
        else:
            # Unix: use lsof and kill
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.split("\n")[1:]:
                if line.strip():
                    parts = line.split()
                    pid = parts[1]
                    try:
                        subprocess.run(["kill", "-9", pid], check=True)
                        print_success(f"Killed process on port {port} (PID: {pid})")
                        return True
                    except subprocess.CalledProcessError as e:
                        logging.debug("Failed to kill process %s on port %d: %s", pid, port, e)
    except Exception as e:
        print_warning(f"Could not kill process on port {port}: {e}")
        return False
    
    return False


def get_hector_db_path():
    """Get the Hector database path."""
    return os.path.join(os.path.dirname(__file__), "hector_db")


def get_indexed_documents_count():
    """Get count of indexed documents from ChromaDB."""
    try:
        import chromadb

        db_path = get_hector_db_path()
        if not os.path.exists(db_path):
            return 0

        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()

        total_count = 0
        for coll in collections:
            try:
                total_count += coll.count()
            except Exception as e:
                logging.debug("Failed to count collection: %s", e)

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
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(books_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            books.append({
                "name": file,
                "path": file_path,
                "size": size_mb,
            })

    return books


def resolve_command(command_name: str) -> str:
    """Resolve a command from PATH with a Windows-friendly fallback."""
    if sys.platform == "win32":
        resolved = shutil.which(f"{command_name}.cmd") or shutil.which(command_name)
    else:
        resolved = shutil.which(command_name)

    if not resolved:
        raise FileNotFoundError(f"Could not find '{command_name}' on PATH")

    return resolved


def cmd_init(args):
    """Initialize and start HECTOR (Backend + Frontend)."""
    import time

    import requests

    port = args.port
    frontend_port = args.frontend_port
    no_frontend = args.no_frontend
    auto_port = args.auto_port
    kill_existing = args.kill_existing
    project_dir = os.path.dirname(__file__)
    frontend_dir = os.path.join(project_dir, "frontend")
    api_process = None
    frontend_process = None

    # Check and handle port conflicts
    if not is_port_available(port):
        print_warning(f"Port {port} is already in use")
        if kill_existing:
            print_info(f"Attempting to kill process on port {port}...")
            if kill_process_on_port(port):
                import time
                time.sleep(1)  # Give time for port to be released
            else:
                print_error(f"Could not free port {port}. Try using --auto-port or --port with a different value")
                return
        elif auto_port:
            new_port = find_available_port(port)
            if new_port:
                print_warning(f"Using alternative port {new_port} instead of {port}")
                port = new_port
            else:
                print_error(f"Could not find available port starting from {port}")
                return
        else:
            print_error(
                f"Port {port} is already in use",
                "Use --auto-port to use next available port, or --kill-existing to terminate the existing process"
            )
            return

    if not no_frontend and not is_port_available(frontend_port):
        print_warning(f"Frontend port {frontend_port} is already in use")
        if kill_existing:
            print_info(f"Attempting to kill process on port {frontend_port}...")
            if kill_process_on_port(frontend_port):
                import time
                time.sleep(1)  # Give time for port to be released
            else:
                print_error(f"Could not free port {frontend_port}. Try using --auto-port or --frontend-port with a different value")
                return
        elif auto_port:
            new_port = find_available_port(frontend_port)
            if new_port:
                print_warning(f"Using alternative port {new_port} for frontend instead of {frontend_port}")
                frontend_port = new_port
            else:
                print_error(f"Could not find available port starting from {frontend_port}")
                return
        else:
            print_error(
                f"Frontend port {frontend_port} is already in use",
                "Use --auto-port to use next available port, or --kill-existing to terminate the existing process"
            )
            return

    def wait_for_http(url: str, label: str, process, headers=None, accepted_statuses=(200,)) -> bool:
        max_retries = 30

        for attempt in range(max_retries):
            if process is not None and process.poll() is not None:
                print_error(f"{label} stopped before it became ready", f"Exit code: {process.returncode}")
                return False

            try:
                response = requests.get(url, timeout=1, headers=headers)
                if response.status_code in accepted_statuses:
                    print_success(f"{label} running on {url}")
                    return True
            except Exception as e:
                logging.debug("HTTP request to %s failed: %s", url, e)

            time.sleep(1)

            if attempt == max_retries - 1:
                print_warning(f"{label} might not be ready yet")

        return False

    print("\n" + "=" * 60)
    print("H.E.C.T.O.R. INITIALIZATION")
    print("=" * 60)

    try:
        print("\nStarting API Server...")
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        
        # Save process information
        save_process_info(port, frontend_port, api_process.pid)

        if not wait_for_http(
            url=f"http://localhost:{port}/docs",
            label="API Server",
            process=api_process,
            accepted_statuses=(200,),
        ):
            return

        if not no_frontend:
            print("\nStarting Frontend Dev Server...")

            if not os.path.exists(frontend_dir):
                print_warning("Frontend directory not found")
            else:
                frontend_env = os.environ.copy()
                frontend_env["PORT"] = str(frontend_port)
                frontend_env.setdefault("NODE_OPTIONS", "--max-old-space-size=4096")

                frontend_process = subprocess.Popen(
                    [resolve_command("npm"), "run", "dev", "--", "--port", str(frontend_port)],
                    cwd=frontend_dir,
                    env=frontend_env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                )
                
                # Save frontend process info
                save_process_info(port, frontend_port, frontend_process.pid)

                if not wait_for_http(
                    url=f"http://localhost:{frontend_port}",
                    label="Frontend",
                    process=frontend_process,
                    accepted_statuses=(200, 304),
                ):
                    return

        print("\n" + "=" * 60)
        print_success("HECTOR is now running!")
        print(f"- API: http://localhost:{port}")
        if not no_frontend:
            print(f"- Frontend: http://localhost:{frontend_port}")
        print("- Press Ctrl+C to stop all services")
        print("=" * 60 + "\n")

        while True:
            import time
            time.sleep(1)
            if api_process.poll() is not None:
                print_error("API server stopped unexpectedly", f"Exit code: {api_process.returncode}")
                break
            if frontend_process and frontend_process.poll() is not None and not no_frontend:
                print_error("Frontend server stopped unexpectedly", f"Exit code: {frontend_process.returncode}")
                break
    except KeyboardInterrupt:
        print("\n\nStopping services...")
    except FileNotFoundError as e:
        print_error("Required command not found", str(e))
        print_info("Make sure Node.js and npm are installed for frontend")
    except Exception as e:
        print_error("Failed to start services", str(e))
    finally:
        print("\nShutting down services...")
        
        # Terminate gracefully first
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                api_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        # Clean up any stuck processes on the ports
        import time
        time.sleep(0.5)
        cleanup_stuck_ports([port, frontend_port] if not no_frontend else [port])
        
        # Clear process info
        clear_process_info()
        
        print_success("All services stopped")


def cmd_ingest(args):
    """Ingest books from data/Books directory."""
    print("\n" + "=" * 60)
    print("H.E.C.T.O.R. INGESTION")
    print("=" * 60)

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
        print(f"  - {book['name']} ({book['size']:.2f} MB)")

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
    print("\n" + "=" * 60)
    print("H.E.C.T.O.R. SYSTEM STATUS")
    print("=" * 60)

    db_path = get_hector_db_path()
    db_exists = os.path.exists(db_path)
    total_docs = get_indexed_documents_count() if db_exists else 0

    print("\n[Database]")
    print(f"  Status: {'Connected' if db_exists else 'Not Found'}")
    print(f"  Total Documents: {total_docs}")

    books_dir = os.path.join(os.path.dirname(__file__), "data", "Books")
    available_books = get_available_books()

    print("\n[Books]")
    print(f"  Available: {len(available_books)}")
    print(f"  Directory: {books_dir}")

    if available_books:
        print("\n[Book List]")
        for book in available_books:
            print(f"  - {book['name']} ({book['size']:.2f} MB)")

    print("\n[Environment]")
    try:
        import chromadb  # noqa: F401
        print("  ChromaDB: [+] Installed")
    except ImportError:
        print("  ChromaDB: [X] Not installed")

    try:
        import fastapi  # noqa: F401
        print("  FastAPI: [+] Installed")
    except ImportError:
        print("  FastAPI: [X] Not installed")

    try:
        import sentence_transformers  # noqa: F401
        print("  Embeddings: [+] Installed")
    except ImportError:
        print("  Embeddings: [X] Not installed")


def cmd_help(args):
    """Display help message."""
    print(
        """
HECTOR - Legal Intelligence System

Commands:
  hector init                    Start HECTOR (API + Frontend)
    --port, -p PORT              API port (default: 8000)
    --frontend-port, -fp PORT    Frontend port (default: 3000)
    --no-frontend                Start only backend API
    --auto-port                  Auto-detect available ports if in use
    --kill-existing              Kill existing processes on ports

  hector ingest                  Ingest books from data/Books

  hector status                  Display system status

  hector --help                  Show this help message

Examples:
  hector init                    Start the application
  hector init --no-frontend      Start backend only
  hector init --port 9000        Use custom API port
  hector init --auto-port        Auto-detect available ports
  hector ingest                  Ingest new books
  hector status                  Check system status
  hector --help                  Show help
"""
    )


def cmd_ps(args):
    """List ongoing HECTOR processes."""
    proc_info = load_process_info()
    
    if not proc_info or 'pids' not in proc_info or not proc_info['pids']:
        print_warning("No active HECTOR processes found")
        return
    
    print("\n" + "=" * 60)
    print("ACTIVE HECTOR PROCESSES")
    print("=" * 60)
    
    if 'last_api_port' in proc_info:
        print(f"\nAPI Port: {proc_info['last_api_port']}")
        print(f"  URL: http://localhost:{proc_info['last_api_port']}")
    
    if 'last_frontend_port' in proc_info:
        print(f"\nFrontend Port: {proc_info['last_frontend_port']}")
        print(f"  URL: http://localhost:{proc_info['last_frontend_port']}")
    
    print(f"\nProcess IDs: {', '.join(map(str, proc_info.get('pids', [])))}")
    print("\n" + "=" * 60)


def cmd_kill(args):
    """Kill stuck HECTOR processes."""
    proc_info = load_process_info()
    
    ports = []
    if 'last_api_port' in proc_info:
        ports.append(proc_info['last_api_port'])
    if 'last_frontend_port' in proc_info:
        ports.append(proc_info['last_frontend_port'])
    
    if not ports:
        print_warning("No ports recorded for HECTOR")
        return
    
    print(f"\nKilling processes on ports: {', '.join(map(str, ports))}")
    cleanup_stuck_ports(ports)
    clear_process_info()
    print_success("Cleanup complete")


def cmd_search(args):
    """Search the legal corpus."""
    import httpx
    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/search",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={"query": args.query, "page": args.page, "page_size": args.size, "verify": not args.no_verify, "format": args.format, "include_related": True},
            )
            resp.raise_for_status()
            data = resp.json()
        print(f"\nQuery: {args.query}")
        print(f"Route: {data.get('route', 'N/A')}")
        print(f"Confidence: {data.get('answer_confidence', 0)}%")
        for i, item in enumerate(data.get("items", []), 1):
            print(f"  {i}. [{item.get('act', '?')}] {item.get('snippet', '')[:100]}... (score: {item.get('similarity_score', 0):.2f})")
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        sys.exit(1)


def cmd_compare(args):
    """Compare IPC ↔ BNS sections."""
    import httpx
    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/compare",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={"section": args.section, "act": args.act, "page_size": args.size},
            )
            resp.raise_for_status()
            data = resp.json()
        counterpart = "BNS" if args.act.upper() == "IPC" else "IPC"
        print(f"\nRequested: {args.act} Section {data.get('requested_section', args.section)}")
        print(f"Counterpart: {counterpart} Section {data.get('counterpart_section', '?')}")
        print(f"Note: {data.get('note', 'N/A')}")
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        sys.exit(1)


def cmd_deep_cite(args):
    """Deep citation verification."""
    import httpx
    api_url = os.getenv("HECTOR_API_URL", "http://localhost:8000")
    api_key = os.getenv("HECTOR_API_KEY", "")
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{api_url}/search",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={"query": args.query, "page": 1, "page_size": 10, "verify": True, "format": "citations", "include_related": True},
            )
            resp.raise_for_status()
            data = resp.json()
        print(f"\nQuery: {args.query}")
        print(f"Confidence: {data.get('answer_confidence', 0)}%")
        for i, src in enumerate(data.get("source_sections", []), 1):
            print(f"  {i}. {src.get('section', '?')} {src.get('act', '')} ({src.get('similarity', 0):.1%})")
    except httpx.HTTPError as e:
        print_error("API request failed", str(e))
        sys.exit(1)


def main():
    """Main entry point."""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        cmd_help(None)
        return

    parser = argparse.ArgumentParser(
        description="HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval",
        add_help=False,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Start HECTOR (API + Frontend)")
    init_parser.add_argument("--port", "-p", type=int, default=8000, help="API server port")
    init_parser.add_argument("--frontend-port", "-fp", type=int, default=3000, help="Frontend port")
    init_parser.add_argument("--no-frontend", action="store_true", help="Start only backend API")
    init_parser.add_argument("--auto-port", action="store_true", help="Automatically use next available port if default is in use")
    init_parser.add_argument("--kill-existing", action="store_true", help="Kill existing process on the port if it's in use")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest books from data/Books")
    ingest_parser.add_argument("--force", "-f", action="store_true", help="Re-ingest all books")
    ingest_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed progress")

    subparsers.add_parser("status", help="Display system status")
    subparsers.add_parser("help", help="Show this help message")

    search_parser = subparsers.add_parser("search", help="Search the legal corpus")
    search_parser.add_argument("query", help="Legal query to search")
    search_parser.add_argument("--page", "-p", type=int, default=1, help="Page number")
    search_parser.add_argument("--size", "-s", type=int, default=5, help="Results per page")
    search_parser.add_argument("--format", "-f", default="summary", choices=["summary", "detailed", "citations"], help="Output format")
    search_parser.add_argument("--no-verify", action="store_true", help="Skip verification")

    compare_parser = subparsers.add_parser("compare", help="Compare IPC ↔ BNS sections")
    compare_parser.add_argument("section", help="Section number to compare")
    compare_parser.add_argument("--act", "-a", default="IPC", choices=["IPC", "BNS"], help="Act")
    compare_parser.add_argument("--size", "-s", type=int, default=3, help="Results per side")

    deepcite_parser = subparsers.add_parser("deep-cite", help="Deep citation verification")
    deepcite_parser.add_argument("query", help="Legal query for deep citation analysis")

    subparsers.add_parser("ps", help="List ongoing HECTOR processes")
    subparsers.add_parser("kill", help="Kill stuck HECTOR processes")

    args = parser.parse_args()

    if args.command is None:
        cmd_help(None)
        return

    try:
        if args.command == "init":
            cmd_init(args)
        elif args.command == "ingest":
            cmd_ingest(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "search":
            cmd_search(args)
        elif args.command == "compare":
            cmd_compare(args)
        elif args.command == "deep-cite":
            cmd_deep_cite(args)
        elif args.command == "help":
            cmd_help(args)
        elif args.command == "ps":
            cmd_ps(args)
        elif args.command == "kill":
            cmd_kill(args)
    except KeyboardInterrupt:
        print("\n")
        sys.exit(0)
    except Exception as e:
        print(f"[X] Command failed: {args.command}")
        print(f"  {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
