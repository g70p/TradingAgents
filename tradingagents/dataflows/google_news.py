"""Google News RSS — alternativa gratuita ao StockTwits e Reddit.

Fornece notícias via RSS do Google News, sem necessidade de API key.
Usado como fonte complementar de sentimento para o analista.
"""

from __future__ import annotations

import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from .rss_utils import rss_lines

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


def _parse_rss_titles(xml_text: str, limit: int = 20, *, start_date=None, end_date=None) -> list[str]:
    return rss_lines(xml_text, limit, start_date=start_date, end_date=end_date)


def fetch_google_news(query: str, limit: int = 15, language: str = "en", *, start_date: str | None = None, end_date: str | None = None) -> str:
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

    titles = _parse_rss_titles(xml, limit=limit, start_date=start_date, end_date=end_date)
    if not titles:
        return ""

    parts = [f"### Google News: \"{query}\" ({len(titles)} manchetes)\n"]
    for i, title in enumerate(titles, 1):
        parts.append(f"{i}. {title}")

    return "\n".join(parts)


def fetch_google_news_for_ticker(ticker: str, limit: int = 15, *, start_date: str | None = None, end_date: str | None = None) -> str:
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
        result = fetch_google_news(query, limit=5, start_date=start_date, end_date=end_date)
        if result:
            # Don't repeat the header for each query
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([line for line in lines if line.strip()])

    if not all_parts:
        return f"⚠️ Google News: sem resultados para {ticker}."

    # Deduplicate
    seen = set()
    unique = []
    for line in all_parts:
        line = re.sub(r"^\d+\.\s*", "", line)
        if line not in seen:
            seen.add(line)
            unique.append(line)

    header = f"### 📰 Google News para {ticker} ({min(len(unique), limit)} manchetes)\n"
    return header + "\n".join(f"{i}. {line}" for i, line in enumerate(unique[:limit], 1))


def fetch_google_news_sentiment(ticker: str, limit: int = 10, *, start_date: str | None = None, end_date: str | None = None) -> str:
    """Versão PT-PT do fetch de notícias Google News.

    Procura em português e inglês para máxima cobertura.
    """
    base = ticker.split("-")[0] if "-" in ticker else ticker
    base = base.split(".")[0] if "." in base else base

    all_parts = []
    queries_pt = [f"{base} cotação", f"{ticker} análise"]
    queries_en = [f"{ticker} news", f"{base} price analysis"]

    for query in queries_pt:
        result = fetch_google_news(query, limit=3, language="pt", start_date=start_date, end_date=end_date)
        if result:
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([line for line in lines if line.strip()])

    for query in queries_en:
        result = fetch_google_news(query, limit=3, language="en", start_date=start_date, end_date=end_date)
        if result:
            lines = result.split("\n")
            if lines and lines[0].startswith("###"):
                lines = lines[1:]
            all_parts.extend([line for line in lines if line.strip()])

    if not all_parts:
        return f"⚠️ Google News indisponível para {ticker}."

    seen = set()
    unique = []
    for line in all_parts:
        line = re.sub(r"^\d+\.\s*", "", line)
        if line not in seen:
            seen.add(line)
            unique.append(line)

    return f"### 📰 Notícias Google para {ticker} ({len(unique[:limit])} manchetes)\n" + "\n".join(unique[:limit])
