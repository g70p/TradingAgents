"""Google News RSS — alternativa gratuita ao StockTwits e Reddit.

Fornece notícias via RSS do Google News, sem necessidade de API key.
Usado como fonte complementar de sentimento para o analista.
"""

from __future__ import annotations

import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def _fetch_rss(url: str, timeout: int = 8) -> str | None:
    """Fetch RSS feed content. Returns raw XML string or None."""
    try:
        req = Request(url, headers={"User-Agent": "TradingAgents/2.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, OSError) as e:
        logger.debug("Google News RSS failed: %s", e)
        return None


def _parse_rss_titles(xml_text: str, limit: int = 20) -> list[str]:
    """Extract titles from RSS XML. Basic parser — no heavy deps."""
    import re
    titles = re.findall(r"<title>(.*?)</title>", xml_text, re.DOTALL)
    # Skip the feed title (first <title>)
    return [
        t.strip().replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
        for t in titles[1:limit + 1] if t.strip()
    ]


def fetch_google_news(query: str, limit: int = 15, language: str = "en") -> str:
    """Fetch news headlines from Google News RSS for a query.

    Args:
        query: Search query (e.g. 'BTC Bitcoin', 'NVDA stock')
        limit: Max headlines to return
        language: 'en' for English, 'pt' for Portuguese

    Returns:
        Markdown-formatted string with headlines, or empty string on failure.
    """
    encoded = quote_plus(query)
    hl = "pt-PT" if language == "pt" else "en-US"
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&ceid={hl}:{language}"

    xml = _fetch_rss(url)
    if not xml:
        return ""

    titles = _parse_rss_titles(xml, limit=limit)
    if not titles:
        return ""

    parts = [f"### Google News: \"{query}\" ({len(titles)} manchetes)\n"]
    for i, title in enumerate(titles, 1):
        parts.append(f"{i}. {title}")

    return "\n".join(parts)


def fetch_google_news_for_ticker(ticker: str, limit: int = 15) -> str:
    """Fetch Google News headlines relevant to a trading ticker.

    Tries multiple query variations to get diverse coverage.
    """
    # Strip exchange suffix for cleaner queries
    base = ticker.split("-")[0] if "-" in ticker else ticker
    base = base.split(".")[0] if "." in base else base

    all_parts = []
    queries = [
        f"{ticker} stock",
        f"{base} price",
        f"{ticker} news today",
    ]

    for query in queries:
        result = fetch_google_news(query, limit=5)
        if result:
            # Don't repeat the header for each query
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([l for l in lines if l.strip()])

    if not all_parts:
        return f"⚠️ Google News: sem resultados para {ticker}."

    # Deduplicate
    seen = set()
    unique = []
    for line in all_parts:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    header = f"### 📰 Google News para {ticker} ({len(unique)} manchetes)\n"
    return header + "\n".join(unique[:limit])


def fetch_google_news_sentiment(ticker: str, limit: int = 10) -> str:
    """Versão PT-PT do fetch de notícias Google News.

    Procura em português e inglês para máxima cobertura.
    """
    base = ticker.split("-")[0] if "-" in ticker else ticker
    base = base.split(".")[0] if "." in base else base

    all_parts = []
    queries_pt = [f"{base} cotação", f"{ticker} análise"]
    queries_en = [f"{ticker} news", f"{base} price analysis"]

    for query in queries_pt:
        result = fetch_google_news(query, limit=3, language="pt")
        if result:
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([l for l in lines if l.strip()])

    for query in queries_en:
        result = fetch_google_news(query, limit=3, language="en")
        if result:
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([l for l in lines if l.strip()])

    if not all_parts:
        return f"⚠️ Google News indisponível para {ticker}."

    seen = set()
    unique = []
    for line in all_parts:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    return f"### 📰 Notícias Google para {ticker} ({len(unique[:limit])} manchetes)\n" + "\n".join(unique[:limit])
