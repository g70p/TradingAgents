"""Agregador de notícias multi-fonte — gratuito, sem API keys.

Fontes (por ordem de prioridade):
  1. Google News (global, PT + EN)
  2. Euronext (comunicados oficiais — empresas listadas)
  3. Jornal de Negócios (PT — finanças nacionais)
  4. Investing.com RSS (global — mercados, cripto, commodities)
  5. CNBC RSS (internacional — EUA, Ásia, Europa)

Todas as fontes são RSS públicas, sem necessidade de autenticação.
Cada fonte tem fallback automático — se uma falhar, tenta a seguinte.
"""

from __future__ import annotations

import logging
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_USER_AGENT = "TradingAgents/2.0 (aggregator; contact: github.com/G70P/TradingAgents)"


def _fetch_rss(url: str, timeout: int = 8) -> str | None:
    """Fetch RSS/XML content. Returns raw text or None."""
    try:
        req = Request(url, headers={"User-Agent": _USER_AGENT})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, OSError, ValueError) as e:
        logger.debug("RSS fetch failed for %s: %s", url[:80], e)
        return None


def _parse_rss_titles(xml_text: str, limit: int = 15) -> list[str]:
    """Extract titles from RSS XML and strip duplicates."""
    titles = re.findall(r"<title>(.*?)</title>", xml_text, re.DOTALL)
    clean = []
    seen = set()
    for t in titles[1:]:  # Skip feed title
        ct = t.strip()
        ct = ct.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        ct = ct.replace("&#39;", "'").replace("&quot;", '"').replace("&#x27;", "'")
        if ct and ct not in seen and ct.lower() not in ("google news", "rss feed"):
            seen.add(ct)
            clean.append(ct)
        if len(clean) >= limit:
            break
    return clean


# ═══════════════════════════════════════════════════════════════════════════════
# Fontes individuais
# ═══════════════════════════════════════════════════════════════════════════════

def _source_google_news(query: str, lang: str = "en", limit: int = 8) -> str | None:
    """Google News RSS."""
    hl = "pt-PT" if lang == "pt" else "en-US"
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={hl}"
    xml = _fetch_rss(url)
    if not xml:
        return None
    titles = _parse_rss_titles(xml, limit)
    return "\n".join(f"- {t}" for t in titles) if titles else None


def _source_euronext(ticker: str, limit: int = 5) -> str | None:
    """Euronext press releases — apenas para tickers .LS, .PA, .AS, .BR.

    Euronext não tem RSS público estável. Usamos o site institucional.
    Fallback: Google News com 'site:euronext.com'.
    """
    if not any(ticker.endswith(s) for s in (".LS", ".PA", ".AS", ".BR", ".LX")):
        return None  # Não é stock Euronext

    base = ticker.split(".")[0]
    # Euronext usa ISIN ou nome da empresa. Tentamos Google News focado.
    query = f"{base} site:euronext.com OR site:live.euronext.com"
    return _source_google_news(query, limit=limit)


def _source_jornal_negocios(ticker: str, limit: int = 5) -> str | None:
    """Jornal de Negócios (negocios.pt) — notícias financeiras portuguesas."""
    base = ticker.split(".")[0] if "." in ticker else ticker
    base = base.split("-")[0] if "-" in base else base
    query = f"{base} site:jornaldenegocios.pt"
    return _source_google_news(query, limit=limit)


def _source_investing(ticker: str, limit: int = 5) -> str | None:
    """Investing.com RSS — cobre acções, cripto, commodities, forex."""
    # Investing.com tem RSS feeds por categoria
    feeds = [
        "https://www.investing.com/rss/news.rss",
        "https://www.investing.com/rss/market_overview.rss",
        "https://www.investing.com/rss/news_25.rss",  # commodities
        "https://www.investing.com/rss/news_301.rss",  # economia
    ]
    all_titles = []
    for feed in feeds:
        xml = _fetch_rss(feed)
        if xml:
            all_titles.extend(_parse_rss_titles(xml, limit=3))

    if not all_titles:
        return None

    seen = set()
    unique = []
    for t in all_titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return "\n".join(f"- {t}" for t in unique[:limit])


def _source_cnbc(limit: int = 5) -> str | None:
    """CNBC RSS — notícias de mercados globais."""
    feeds = [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",  # top news
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",  # economy
    ]
    all_titles = []
    for feed in feeds:
        xml = _fetch_rss(feed, timeout=10)
        if xml:
            titles = _parse_rss_titles(xml, limit=3)
            all_titles.extend(titles)

    if not all_titles:
        return None

    seen = set()
    unique = []
    for t in all_titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return "\n".join(f"- {t}" for t in unique[:limit])


def _source_marketwatch(limit: int = 5) -> str | None:
    """MarketWatch RSS — mercados EUA."""
    feeds = [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    ]
    all_titles = []
    for feed in feeds:
        xml = _fetch_rss(feed, timeout=10)
        if xml:
            titles = _parse_rss_titles(xml, limit=3)
            all_titles.extend(titles)

    if not all_titles:
        return None

    seen = set()
    unique = []
    for t in all_titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return "\n".join(f"- {t}" for t in unique[:limit])


# ═══════════════════════════════════════════════════════════════════════════════
# Agregador principal
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_news_multi_source(ticker: str, limit_per_source: int = 6) -> str:
    """Agrega notícias de múltiplas fontes com fallback automático.

    Args:
        ticker: Ticker (ex: BCP.LS, BTC-USD, NVDA)
        limit_per_source: Máximo de manchetes por fonte

    Returns:
        Markdown com manchetes organizadas por fonte.
    """
    base = ticker.split(".")[0] if "." in ticker else ticker
    base = base.split("-")[0] if "-" in base else base

    is_crypto = ticker.endswith("-USD")
    is_euronext = any(ticker.endswith(s) for s in (".LS", ".PA", ".AS", ".BR", ".LX"))
    is_pt = ticker.endswith(".LS")

    parts = []
    total_news = 0

    # 1. Google News PT (para tickers portugueses) ou EN
    if is_pt:
        pt = _source_google_news(f"{base} cotação", lang="pt", limit=limit_per_source)
        if pt:
            parts.append(f"### 🇵🇹 Google News PT: \"{base}\"\n{pt}")
            total_news += pt.count("\n") + 1

    en = _source_google_news(f"{ticker} stock price analysis", limit=limit_per_source)
    if en:
        parts.append(f"### 🌍 Google News EN: \"{ticker}\"\n{en}")
        total_news += en.count("\n") + 1

    # 2. Euronext (para stocks europeus)
    euronext = _source_euronext(ticker, limit=limit_per_source)
    if euronext:
        parts.append(f"### 🏛️ Euronext: {ticker}\n{euronext}")
        total_news += euronext.count("\n") + 1

    # 3. Jornal de Negócios (para PT)
    negocios = _source_jornal_negocios(ticker, limit=limit_per_source)
    if negocios:
        parts.append(f"### 📰 Jornal de Negócios: {ticker}\n{negocios}")
        total_news += negocios.count("\n") + 1

    # 4. Investing.com (global)
    investing = _source_investing(ticker, limit=limit_per_source)
    if investing:
        parts.append(f"### 📈 Investing.com: mercados\n{investing}")
        total_news += investing.count("\n") + 1

    # 5. CNBC (internacional)
    cnbc = _source_cnbc(limit=limit_per_source)
    if cnbc:
        parts.append(f"### 🇺🇸 CNBC: notícias de mercados\n{cnbc}")
        total_news += cnbc.count("\n") + 1

    # 6. MarketWatch (EUA)
    mw = _source_marketwatch(limit=limit_per_source)
    if mw:
        parts.append(f"### 🇺🇸 MarketWatch: mercados\n{mw}")
        total_news += mw.count("\n") + 1

    if not parts:
        return f"⚠️ Nenhuma fonte de notícias disponível para {ticker}."

    header = f"## 📰 Notícias Agregadas para {ticker} ({total_news} manchetes de {len(parts)} fontes)\n\n"
    return header + "\n\n".join(parts)
