#!/usr/bin/env python3
"""Interactive CLI chat with Shri Mataji knowledge base."""

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from chat.bot import chat

console = Console()


def main():
    console.print("\n[bold cyan]Shri Mataji Chat[/bold cyan]")
    console.print("Type your question. Press [bold]Ctrl+C[/bold] or type [bold]exit[/bold] to quit.\n")

    history = []
    while True:
        try:
            query = Prompt.ask("[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if query.strip().lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        if not query.strip():
            continue

        with console.status("[dim]Searching teachings...[/dim]"):
            answer, history = chat(query, history=history)

        console.print("\n[bold blue]Shri Mataji Bot[/bold blue]")
        console.print(Markdown(answer))
        console.print()


if __name__ == "__main__":
    main()
