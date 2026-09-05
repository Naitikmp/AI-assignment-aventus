import sys
import argparse
from pathlib import Path
from src.policy_agent.workflow import PolicyAssistant
from src.policy_agent.schemas import CoverageVerdict

# Try importing rich for formatted terminal output; fallback to standard print if not installed
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def render_response(response, provider_name: str):
    verdict_colors = {
        CoverageVerdict.COVERED: "green",
        CoverageVerdict.PARTIALLY_COVERED: "yellow",
        CoverageVerdict.OUT_OF_SCOPE: "red",
    }

    if HAS_RICH:
        color = verdict_colors.get(response.verdict, "white")
        badge = f"[{color} bold]{response.verdict.value}[/{color} bold]"
        header = f"Status: {badge}  |  Provider: [cyan]{provider_name}[/cyan]"

        body = f"{response.answer}\n"
        if response.citations:
            body += "\n[bold underline]Source Citations:[/bold underline]\n"
            for c in response.citations:
                body += f"  • [dim]{c}[/dim]\n"

        panel = Panel(
            body.strip(),
            title=f"[bold]Query: {response.query}[/bold]",
            subtitle=header,
            border_style=color,
            expand=False
        )
        console.print(panel)
        console.print()
    else:
        print(f"\n==================================================")
        print(f"Query: {response.query}")
        print(f"Status: {response.verdict.value} | Provider: {provider_name}")
        print(f"--------------------------------------------------")
        print(response.answer)
        if response.citations:
            print(f"\nSource Citations:")
            for c in response.citations:
                print(f"  * {c}")
        print(f"==================================================\n")


def interactive_loop(assistant: PolicyAssistant):
    welcome_msg = (
        "\n==========================================================\n"
        "  Corporate Travel Expense Policy Assistant (Enterprise)   \n"
        "  Type your question below (or 'exit' / 'quit' to close)  \n"
        "==========================================================\n"
    )
    if HAS_RICH:
        console.print(Panel.fit(
            f"[bold green]Corporate Travel Expense Policy Assistant[/bold green]\n"
            f"Active Provider: [cyan bold]{assistant.provider_name}[/cyan bold] | Records Loaded: [yellow]{assistant.stats.records_loaded}[/yellow] "
            f"(Duplicates Purged: [magenta]{assistant.stats.duplicates_removed}[/magenta])\n"
            f"[dim]Type your question or 'exit'/'quit' to leave.[/dim]",
            border_style="blue"
        ))
    else:
        print(welcome_msg)
        print(f"Active Provider: {assistant.provider_name} | Records Loaded: {assistant.stats.records_loaded} (Duplicates Purged: {assistant.stats.duplicates_removed})\n")

    while True:
        try:
            prompt = input("Ask a question > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit", "q"]:
                print("Exiting policy assistant. Goodbye!")
                break

            response = assistant.ask(prompt)
            render_response(response, assistant.provider_name)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Travel Expense Policy Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py \"What is the daily meal limit in UAE?\"\n"
            "  python main.py \"Can I fly business class for an 8-hour flight?\"\n"
            "  python main.py \"What is the taxi allowance in Dubai?\"\n"
            "  python main.py  # Launches interactive REPL mode\n"
        )
    )
    parser.add_argument("query", nargs="?", type=str, help="Single query to evaluate against policy")
    parser.add_argument("--data", type=str, default=None, help="Path to policy CSV dataset (optional)")
    parser.add_argument("--provider", type=str, choices=["local", "azure_openai", "openai"], default=None, help="Override provider (default: local or detected)")

    args = parser.parse_args()

    try:
        assistant = PolicyAssistant(data_path=args.data, provider_name=args.provider)
    except Exception as e:
        print(f"Error initializing PolicyAssistant: {e}", file=sys.stderr)
        sys.exit(1)

    if args.query:
        response = assistant.ask(args.query)
        render_response(response, assistant.provider_name)
    else:
        interactive_loop(assistant)


if __name__ == "__main__":
    main()
