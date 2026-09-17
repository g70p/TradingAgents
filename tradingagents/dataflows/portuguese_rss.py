"""
Portuguese RSS news feeds for TradingAgents.
Fetches headlines from free Portuguese news sources to supplement
global news with local PSI/Euronext Lisbon context.
No API keys required — all sources are open RSS feeds.
"""
from __future__ import annotations

import urllib.request
from datetime import datetime, timezone

from .rss_utils import parse_rss_entries

# Free Portuguese RSS feeds relevant to trading/PSI
FEEDS = {
    "ECO": {
        "url": "https://eco.sapo.pt/feed",
        "description": "Economia e negócios (digital)",
    },
    "Jornal de Negócios": {
        "url": "https://www.jornaldenegocios.pt/rss",
        "description": "Jornal económico português",
    },
    "RTP Notícias": {
        "url": "https://www.rtp.pt/noticias/rss",
        "description": "Rádio e Televisão de Portugal",
    },
}


def _fetch_rss(url: str, limit: int = 10, timeout: int = 10, *,
               start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Keep publication dates and apply the requested window before the limit."""
    import re

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("iso-8859-1")
        articles = parse_rss_entries(text, limit, start_date=start_date, end_date=end_date)
        for article in articles:
            article["summary"] = re.sub(r"<[^>]+>", "", article["summary"])[:300]
        return articles
    except (OSError, ValueError):
        return []


def get_portuguese_news(limit_per_feed: int = 5, *, start_date: str | None = None, end_date: str | None = None) -> str:
    """Fetch recent headlines from Portuguese news RSS feeds.

    Returns a formatted string suitable for injection into the
    global news analyst's context. Empty string if all feeds fail.
    """
    all_articles: list[tuple[str, dict]] = []

    for source_name, feed_info in FEEDS.items():
        articles = _fetch_rss(feed_info["url"], limit=limit_per_feed, start_date=start_date, end_date=end_date)
        for art in articles:
            art["source"] = source_name
            all_articles.append((source_name, art))

    if not all_articles:
        return ""

    # Format as markdown
    now = datetime.now(timezone.utc)
    lines = [
        "## Notícias Portuguesas (RSS)",
        f"_Fontes: ECO, Jornal de Negócios, RTP — {now.strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]

    for source_name, art in all_articles:
        lines.append(f"### {art['title']} (fonte: {source_name})")
        stamp = art["pub_date"].isoformat() if art["pub_date"] else "data indisponível"
        lines.append(f"Publicado: {stamp}")
        if art["summary"]:
            lines.append(art["summary"])
        if art["link"]:
            lines.append(f"Link: {art['link']}")
        lines.append("")

    return "\n".join(lines)
