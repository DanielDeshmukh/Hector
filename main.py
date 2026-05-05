import os
import sys

# Suppress HuggingFace symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.orchestrator import HectorOrchestrator

console = Console()

def display_diagnostic(route_data):
    """Renders a diagnostic table for the routing intent."""
    table = Table(title="Intent Routing Diagnostic", show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Property", style="dim", width=15)
    table.add_column("Value")
    
    table.add_row("Route Path", f"[bold cyan]{route_data.get('route', 'GENERAL')}[/bold cyan]")
    table.add_row("Acknowledgment", f"[italic white]{route_data.get('hector_response', 'Acknowledged.')}[/italic white]")
    
    console.print(table)

def run_hector():
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
        console.print(f"[bold red]System Failure during Initialization:[/bold red] {e}")
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

            # Orchestration with Visual Feedback
            with console.status("[bold blue]Processing Intelligence...", spinner="bouncingBar"):
                # Ensure execute returns a structured object or a clean string
                strategy_result = hector.execute(query)
            
            # Diagnostic & Response Rendering
            # Note: Assuming hector.execute now handles internal logging or returns 
            # a result that isn't just a boolean.
            if strategy_result:
                # If strategy_result is a dict, extract the specific message
                content = strategy_result if isinstance(strategy_result, str) else str(strategy_result)
                
                # Check for the 'True' hallucination and handle it
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
            console.print(f"\n[bold red]Runtime Error:[/bold red] {e}")

if __name__ == "__main__":
    run_hector()