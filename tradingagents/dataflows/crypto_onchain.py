"""Crypto on-chain and derivatives data tools for TradingAgents.

Provides funding rates, open interest, and exchange data from public APIs.
Falls back gracefully when data is unavailable (rate-limited, blocked, etc.).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Symbol mapping: TradingAgents ticker → exchange API symbol
# ---------------------------------------------------------------------------
_BINANCE_SYMBOL_MAP = {
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
    "SOL-USD": "SOLUSDT",
    "XRP-USD": "XRPUSDT",
    "DOGE-USD": "DOGEUSDT",
    "ADA-USD": "ADAUSDT",
    "AVAX-USD": "AVAXUSDT",
    "DOT-USD": "DOTUSDT",
    "MATIC-USD": "MATICUSDT",
    "LINK-USD": "LINKUSDT",
    "UNI-USD": "UNIUSDT",
    "ATOM-USD": "ATOMUSDT",
    "LTC-USD": "LTCUSDT",
    "ETC-USD": "ETCUSDT",
    "BCH-USD": "BCHUSDT",
}


def _to_binance_symbol(ticker: str) -> str | None:
    """Convert TradingAgents ticker to Binance symbol, or try heuristic."""
    if ticker in _BINANCE_SYMBOL_MAP:
        return _BINANCE_SYMBOL_MAP[ticker]
    # Heuristic: strip -USD suffix and add USDT
    if ticker.endswith("-USD"):
        return ticker[:-4] + "USDT"
    return None


def _fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON from a URL with error handling. Returns None on any failure."""
    try:
        req = Request(url, headers={"User-Agent": "TradingAgents/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
        logger.debug("Crypto data fetch failed for %s: %s", url, e)
        return None


def get_funding_rate(ticker: str) -> str:
    """Fetch current funding rate from Binance public API.

    Returns markdown-formatted funding rate information.
    Positive = longs pay shorts (bullish), negative = shorts pay longs (bearish).
    """
    symbol = _to_binance_symbol(ticker)
    if not symbol:
        return f"⚠️ **Funding Rate indisponível**: '{ticker}' não é reconhecido como par cripto Binance."

    data = _fetch_json("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=10)
    if not data:
        # Try single symbol endpoint
        data = _fetch_json(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}")

    if isinstance(data, dict) and "lastFundingRate" in data:
        rate = float(data["lastFundingRate"]) * 100
        direction = "🟢 Longs pagam Shorts (bullish)" if rate > 0 else "🔴 Shorts pagam Longs (bearish)" if rate < 0 else "⚪ Neutro"
        return (
            f"📊 **Funding Rate para {ticker} ({symbol}):**\n\n"
            f"- **Taxa atual**: {rate:.4f}% (a cada 8h)\n"
            f"- **Taxa anualizada**: ~{abs(rate) * 3 * 365:.1f}%/ano\n"
            f"- **Direção**: {direction}\n"
            f"- **Mark Price**: {data.get('markPrice', 'N/A')}\n"
            f"- **Índice**: {data.get('indexPrice', 'N/A')}"
        )

    if isinstance(data, list):
        for item in data:
            if item.get("symbol") == symbol:
                rate = float(item["lastFundingRate"]) * 100
                direction = "🟢 Longs pagam Shorts" if rate > 0 else "🔴 Shorts pagam Longs" if rate < 0 else "⚪ Neutro"
                return (
                    f"📊 **Funding Rate para {ticker} ({symbol}):**\n\n"
                    f"- **Taxa atual**: {rate:.4f}% (a cada 8h)\n"
                    f"- **Direção**: {direction}\n"
                    f"- **Mark Price**: {item.get('markPrice', 'N/A')}"
                )

    return f"⚠️ **Funding Rate indisponível** para {ticker}: API da Binance não retornou dados."


def get_open_interest(ticker: str) -> str:
    """Fetch open interest from Binance Futures public API.

    Returns markdown-formatted open interest data with 24h change.
    """
    symbol = _to_binance_symbol(ticker)
    if not symbol:
        return f"⚠️ **Open Interest indisponível**: '{ticker}' não é reconhecido."

    data = _fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}")
    if not data:
        return f"⚠️ **Open Interest indisponível** para {ticker}."

    oi = float(data.get("openInterest", 0))
    oi_value = oi  # in USDT (contract size is in the underlying)

    # Fetch 24h change via klines
    klines = _fetch_json(
        f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=2"
    )
    change_24h = "N/A"
    if isinstance(klines, list) and len(klines) >= 2:
        prev_close = float(klines[0][4])
        curr_price = float(klines[1][4])
        if prev_close > 0:
            change_24h = f"{((curr_price - prev_close) / prev_close) * 100:+.2f}%"

    return (
        f"📊 **Open Interest para {ticker} ({symbol}):**\n\n"
        f"- **OI Total**: {oi:,.0f} contratos\n"
        f"- **Variação 24h (preço)**: {change_24h}\n"
        f"- **Nota**: OI elevado com funding positivo = mercado alavancado long (cuidado com squeezes). "
        f"OI a cair = liquidações ou saída de capital."
    )


def get_long_short_ratio(ticker: str) -> str:
    """Fetch long/short ratio from Binance Futures.

    Returns markdown-formatted ratio data.
    """
    symbol = _to_binance_symbol(ticker)
    if not symbol:
        return f"⚠️ **Rácio Long/Short indisponível**: '{ticker}' não é reconhecido."

    # Try global and per-symbol
    data = _fetch_json(
        f"https://fapi.binance.com/fapi/v1/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
    )
    if not data:
        return f"⚠️ **Rácio Long/Short indisponível** para {ticker}."

    if isinstance(data, list) and len(data) > 0:
        ratio = float(data[0]["longShortRatio"])
        long_pct = (ratio / (1 + ratio)) * 100
        short_pct = 100 - long_pct

        if long_pct > 65:
            signal = "⚠️ Maioria esmagadora long — risco de squeeze/liquidação em cascata se o preço cair"
        elif long_pct > 55:
            signal = "🟢 Ligeira maioria long — sentimento positivo mas não extremo"
        elif long_pct < 35:
            signal = "⚠️ Maioria short — possível short squeeze se o preço subir"
        elif long_pct < 45:
            signal = "🔴 Ligeira maioria short — sentimento negativo"
        else:
            signal = "⚪ Equilibrado — sem viés direcional claro"

        return (
            f"📊 **Rácio Long/Short para {ticker} ({symbol}):**\n\n"
            f"- **Long/Short Ratio**: {ratio:.2f}\n"
            f"- **Long**: {long_pct:.1f}% | **Short**: {short_pct:.1f}%\n"
            f"- **Sinal**: {signal}"
        )

    return f"⚠️ **Rácio Long/Short indisponível** para {ticker}."


def get_crypto_onchain_summary(ticker: str) -> str:
    """Aggregate all available crypto on-chain/derivatives data.

    Returns a comprehensive markdown summary for injection into analyst prompts.
    Falls back gracefully when individual data sources are unavailable.
    """
    if not ticker.endswith("-USD") and not ticker.endswith("USD"):
        return ""  # Not a crypto ticker

    parts = [f"## 📊 Dados On-Chain e Derivados para {ticker}\n"]

    funding = get_funding_rate(ticker)
    if "indisponível" not in funding.lower():
        parts.append(funding)
        parts.append("")

    oi = get_open_interest(ticker)
    if "indisponível" not in oi.lower():
        parts.append(oi)
        parts.append("")

    ls = get_long_short_ratio(ticker)
    if "indisponível" not in ls.lower():
        parts.append(ls)
        parts.append("")

    if len(parts) == 1:
        return f"⚠️ Dados on-chain indisponíveis para {ticker} (APIs externas não responderam).\n"

    # Add interpretation guidance
    parts.append(
        "---\n"
        "**Guia de Interpretação:**\n"
        "- **Funding positivo + OI alto + maioria long** = Mercado sobre-alavancado long → risco de correção\n"
        "- **Funding negativo + OI alto + maioria short** = Potencial short squeeze → risco de alta violenta\n"
        "- **OI a cair significativamente** = Saída de capital → fraqueza da tendência\n"
        "- **Funding neutro + OI estável** = Mercado saudável, sem extremos\n"
    )

    return "\n".join(parts)
