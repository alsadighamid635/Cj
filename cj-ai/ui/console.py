"""
Terminal UI using Rich for styled output.
Falls back to plain print if Rich is not installed.
"""

try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich.syntax import Syntax
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

import config


class Console:
    def __init__(self):
        if HAS_RICH:
            self._rc = RichConsole()
        else:
            self._rc = None

    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------

    def show_banner(self):
        if HAS_RICH:
            title = Text()
            title.append(f"\n  {config.APP_NAME}\n", style="bold cyan")
            title.append(f"  {config.APP_SUBTITLE}\n", style="bold white")
            title.append(f"  Version {config.APP_VERSION}\n", style="dim")
            self._rc.print(Panel(title, border_style="cyan", box=box.DOUBLE))
        else:
            print("=" * 55)
            print(f"  {config.APP_NAME}")
            print(f"  {config.APP_SUBTITLE}")
            print(f"  Version {config.APP_VERSION}")
            print("=" * 55)

    # ------------------------------------------------------------------
    # Response output
    # ------------------------------------------------------------------

    def print_response(self, text: str):
        if HAS_RICH:
            self._rc.print()
            # Split code blocks (lines starting with │ or inside [COMMAND: ...] blocks)
            if text.startswith("[COMMAND:"):
                self._print_command_block(text)
            else:
                self._rc.print(Text(text, style="white"), highlight=False)
            self._rc.print()
        else:
            print()
            print(text)
            print()

    def _print_command_block(self, text: str):
        lines = text.split("\n")
        header = lines[0] if lines else ""
        self._rc.print(Rule(title=header, style="green"))
        for line in lines[1:]:
            if line.strip().startswith("│"):
                # It's a command line — print in green bold
                self._rc.print(f"  [bold green]{line.strip()}[/bold green]")
            elif line.strip().startswith("┌") or line.strip().startswith("└"):
                self._rc.print(f"  [dim]{line.strip()}[/dim]")
            elif line.startswith("  ["):
                self._rc.print(f"[yellow]{line}[/yellow]")
            else:
                self._rc.print(line)

    # ------------------------------------------------------------------
    # Input prompt
    # ------------------------------------------------------------------

    def get_input(self) -> str:
        if HAS_RICH:
            self._rc.print("[bold cyan]You >[/bold cyan] ", end="")
        else:
            print("You > ", end="")
        try:
            return input().strip()
        except EOFError:
            return "exit"

    # ------------------------------------------------------------------
    # Info / error messages
    # ------------------------------------------------------------------

    def print_info(self, message: str):
        if HAS_RICH:
            self._rc.print(f"[dim]{message}[/dim]")
        else:
            print(message)

    def print_error(self, message: str):
        if HAS_RICH:
            self._rc.print(f"[bold red]Error:[/bold red] {message}")
        else:
            print(f"Error: {message}")
