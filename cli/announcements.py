import getpass

import requests
from rich.console import Console
from rich.panel import Panel

from cli.config import CLI_CONFIG


# ── Custom fallback — makes it clear this is a fork with different methodology ──
_OUR_FALLBACK = (
    "[cyan]TradingAgents PT-PT[/cyan] — fork com alterações substanciais.\n"
    "Deep thinking em todos os agentes · debate 3 rondas · ATR sizing · crypto on-chain.\n"
    "[dim]Original:[/dim] [link=https://github.com/TauricResearch]github.com/TauricResearch[/link]  |  "
    "[dim]Fork:[/dim] [link=https://github.com/G70P/TradingAgents]github.com/G70P/TradingAgents[/link]"
)


def fetch_announcements(url: str = None, timeout: float = None) -> dict:
    """Fetch announcements from endpoint. Returns dict with announcements and settings."""
    endpoint = url or CLI_CONFIG["announcements_url"]
    timeout = timeout or CLI_CONFIG["announcements_timeout"]

    try:
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return {
            "announcements": data.get("announcements", [_OUR_FALLBACK]),
            "require_attention": data.get("require_attention", False),
        }
    except Exception:
        return {
            "announcements": [_OUR_FALLBACK],
            "require_attention": False,
        }


def display_announcements(console: Console, data: dict) -> None:
    """Display announcements panel. Prompts for Enter if require_attention is True."""
    announcements = data.get("announcements", [])
    require_attention = data.get("require_attention", False)

    if not announcements:
        return

    content = "\n".join(announcements)

    panel = Panel(
        content,
        border_style="cyan",
        padding=(1, 2),
        title="Avisos",
    )
    console.print(panel)

    if require_attention:
        getpass.getpass("Pressiona Enter para continuar...")
    else:
        console.print()
