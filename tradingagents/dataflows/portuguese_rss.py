"""
Portuguese RSS news feeds for TradingAgents.
Fetches headlines from free Portuguese news sources to supplement
global news with local PSI/Euronext Lisbon context.
No API keys required — all sources are open RSS feeds.
"""
from __future__ import annotations

import contextlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

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


def _fetch_rss(url: str, limit: int = 10, timeout: int = 10) -> list[dict]:
    """Fetch and parse an RSS feed, returning article dicts."""
    articles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read()

        # Try common Portuguese encodings
        text = None
        for enc in ["utf-8", "iso-8859-1", "cp1252", "latin-1"]:
            try:
                text = raw.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if text is None:
            text = raw.decode("utf-8", errors="replace")

        root = ET.fromstring(text)

        for item in root.iter("item"):
            if len(articles) >= limit:
                break

            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            date_el = item.find("pubDate")

            title = ""
            if title_el is not None and title_el.text:
                title = title_el.text.strip()
                # Clean CDATA wrapper if present
                if title.startswith("<![CDATA[") and title.endswith("]]>"):
                    title = title[9:-3]

            link = ""
            if link_el is not None:
                if link_el.text:
                    link = link_el.text.strip()
                elif link_el.attrib:  # atom:link with href
                    link = link_el.attrib.get("href", "")

            summary = ""
            if desc_el is not None and desc_el.text:
                summary = desc_el.text.strip()
                if summary.startswith("<![CDATA[") and summary.endswith("]]>"):
                    summary = summary[9:-3]
                # Strip HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary)
                if len(summary) > 300:
                    summary = summary[:297] + "..."

            pub_date = None
            if date_el is not None and date_el.text:
                date_str = date_el.text.strip()
                for fmt in [
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%SZ",
                ]:
                    with contextlib.suppress(ValueError):
                        pub_date = datetime.strptime(date_str, fmt)
                        break

            if title:
                articles.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "pub_date": pub_date,
                })

    except Exception:
        pass  # Feed failure should not crash the whole news fetch

    return articles


def get_portuguese_news(limit_per_feed: int = 5) -> str:
    """Fetch recent headlines from Portuguese news RSS feeds.

    Returns a formatted string suitable for injection into the
    global news analyst's context. Empty string if all feeds fail.
    """
    all_articles: list[tuple[str, dict]] = []

    for source_name, feed_info in FEEDS.items():
        articles = _fetch_rss(feed_info["url"], limit=limit_per_feed)
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
        if art["summary"]:
            lines.append(art["summary"])
        if art["link"]:
            lines.append(f"Link: {art['link']}")
        lines.append("")

    return "\n".join(lines)
