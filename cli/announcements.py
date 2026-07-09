"""Painel de avisos do TradingAgents PT-PT (fork G70P)."""

from rich.console import Console
from rich.panel import Panel

_OUR_MESSAGE = (
    "[bold green]TradingAgents PT-PT[/bold green] — fork com alterações substanciais.\n"
    "Deep thinking em todos os agentes · debate 3 rondas · ATR sizing · crypto on-chain.\n"
    "[dim]Original:[/dim] [link=https://github.com/TauricResearch]github.com/TauricResearch[/link]  |  "
    "[dim]Fork:[/dim] [link=https://github.com/G70P/TradingAgents]github.com/G70P/TradingAgents[/link]"
)


def fetch_announcements() -> dict:
    """Devolve o aviso personalizado do fork (sem dependência externa)."""
    return {
        "announcements": [_OUR_MESSAGE],
        "require_attention": False,
    }


def display_announcements(console: Console, data: dict) -> None:
    """Mostra o painel de avisos."""
    announcements = data.get("announcements", [])
    if not announcements:
        return

    panel = Panel(
        "\n".join(announcements),
        border_style="cyan",
        padding=(1, 2),
        title="Avisos",
    )
    console.print(panel)
    console.print()
