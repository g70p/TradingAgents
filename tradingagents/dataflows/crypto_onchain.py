"""Crypto on-chain, derivatives, and market data for TradingAgents.

Multi-exchange architecture with automatic fallback:
  Binance → Bybit → OKX

Data sources per category:
  - Derivatives (funding rate, OI, L/S ratio): Binance → Bybit → OKX
  - Market data (dominance, market cap): CoinGecko (free API)
  - BTC network (hashrate, mempool): Blockchain.com (free API)

Each function falls back gracefully when a source is unavailable.
All URLs are public, no API keys required.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Symbol mapping: TradingAgents ticker → exchange-specific symbol
# ---------------------------------------------------------------------------
_BINANCE_SYMBOL_MAP = {
    "BTC-USD": "BTCUSDT", "ETH-USD": "ETHUSDT", "SOL-USD": "SOLUSDT",
    "XRP-USD": "XRPUSDT", "DOGE-USD": "DOGEUSDT", "ADA-USD": "ADAUSDT",
    "AVAX-USD": "AVAXUSDT", "DOT-USD": "DOTUSDT", "LINK-USD": "LINKUSDT",
    "LTC-USD": "LTCUSDT", "BCH-USD": "BCHUSDT", "ETC-USD": "ETCUSDT",
    "MATIC-USD": "MATICUSDT", "UNI-USD": "UNIUSDT", "ATOM-USD": "ATOMUSDT",
    "SUI-USD": "SUIUSDT", "APT-USD": "APTUSDT", "ARB-USD": "ARBUSDT",
    "OP-USD": "OPUSDT", "NEAR-USD": "NEARUSDT", "FIL-USD": "FILUSDT",
}
# Bybit uses the same symbol format as Binance (BTCUSDT)
_BYBIT_SYMBOL_MAP = _BINANCE_SYMBOL_MAP
# OKX uses dash format (BTC-USDT-SWAP for perpetuals)
_OKX_SYMBOL_MAP = {
    "BTC-USD": "BTC-USDT-SWAP", "ETH-USD": "ETH-USDT-SWAP",
    "SOL-USD": "SOL-USDT-SWAP", "XRP-USD": "XRP-USDT-SWAP",
    "DOGE-USD": "DOGE-USDT-SWAP", "ADA-USD": "ADA-USDT-SWAP",
    "AVAX-USD": "AVAX-USDT-SWAP", "DOT-USD": "DOT-USDT-SWAP",
    "LINK-USD": "LINK-USDT-SWAP", "LTC-USD": "LTC-USDT-SWAP",
    "BCH-USD": "BCH-USDT-SWAP", "SUI-USD": "SUI-USDT-SWAP",
    "APT-USD": "APT-USDT-SWAP", "ARB-USD": "ARB-USDT-SWAP",
    "OP-USD": "OP-USDT-SWAP", "NEAR-USD": "NEAR-USDT-SWAP",
    "FIL-USD": "FIL-USDT-SWAP",
}

# CoinGecko ID mapping (different from tickers)
_COINGECKO_IDS = {
    "BTC-USD": "bitcoin", "ETH-USD": "ethereum", "SOL-USD": "solana",
    "XRP-USD": "ripple", "DOGE-USD": "dogecoin", "ADA-USD": "cardano",
    "AVAX-USD": "avalanche-2", "DOT-USD": "polkadot", "LINK-USD": "chainlink",
    "LTC-USD": "litecoin", "BCH-USD": "bitcoin-cash", "MATIC-USD": "matic-network",
    "UNI-USD": "uniswap", "ATOM-USD": "cosmos", "SUI-USD": "sui",
    "NEAR-USD": "near", "FIL-USD": "filecoin", "APT-USD": "aptos",
    "ARB-USD": "arbitrum", "OP-USD": "optimism",
}


def _to_exchange_symbol(ticker: str, exchange: str) -> str | None:
    """Convert TradingAgents ticker to exchange-specific symbol."""
    if exchange == "binance":
        sym = _BINANCE_SYMBOL_MAP.get(ticker)
        if not sym and ticker.endswith("-USD"):
            sym = ticker[:-4] + "USDT"
        return sym
    elif exchange == "bybit":
        sym = _BYBIT_SYMBOL_MAP.get(ticker)
        if not sym and ticker.endswith("-USD"):
            sym = ticker[:-4] + "USDT"
        return sym
    elif exchange == "okx":
        sym = _OKX_SYMBOL_MAP.get(ticker)
        if not sym and ticker.endswith("-USD"):
            sym = ticker[:-4] + "-USDT-SWAP"
        return sym
    return None


def _fetch_json(url: str, timeout: int = 10) -> Any | None:
    """Fetch JSON from a URL. Returns None on any failure."""
    try:
        req = Request(url, headers={"User-Agent": "TradingAgents/2.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
        logger.debug("Fetch failed for %s: %s", url, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Funding Rate — multi-exchange with fallback
# ═══════════════════════════════════════════════════════════════════════════════

def _get_funding_rate_binance(symbol: str) -> dict | None:
    data = _fetch_json("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=10)
    if isinstance(data, list):
        for item in data:
            if item.get("symbol") == symbol:
                return {"rate": float(item["lastFundingRate"]) * 100, "mark": item.get("markPrice", "N/A"), "exchange": "Binance"}
    if isinstance(data, dict) and "lastFundingRate" in data:
        return {"rate": float(data["lastFundingRate"]) * 100, "mark": data.get("markPrice", "N/A"), "exchange": "Binance"}
    return None


def _get_funding_rate_bybit(symbol: str) -> dict | None:
    data = _fetch_json(f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}", timeout=10)
    if isinstance(data, dict) and data.get("retCode") == 0:
        result = data.get("result", {}).get("list", [{}])[0]
        rate = float(result.get("fundingRate", 0)) * 100
        return {"rate": rate, "mark": result.get("markPrice", "N/A"), "exchange": "Bybit"}
    return None


def _get_funding_rate_okx(symbol: str) -> dict | None:
    data = _fetch_json(f"https://www.okx.com/api/v5/public/funding-rate?instId={symbol}", timeout=10)
    if isinstance(data, dict) and data.get("code") == "0":
        items = data.get("data", [])
        if items:
            rate = float(items[0].get("fundingRate", 0)) * 100
            return {"rate": rate, "mark": "N/A", "exchange": "OKX"}
    return None


_FUNDING_FETCHERS = [_get_funding_rate_binance, _get_funding_rate_bybit, _get_funding_rate_okx]


def get_funding_rate(ticker: str) -> str:
    """Fetch current funding rate with multi-exchange fallback."""
    for exchange in ["binance", "bybit", "okx"]:
        symbol = _to_exchange_symbol(ticker, exchange)
        if not symbol:
            continue
        fetcher = _FUNDING_FETCHERS[["binance", "bybit", "okx"].index(exchange)]
        result = fetcher(symbol)
        if result:
            rate = result["rate"]
            direction = "🟢 Longs pagam Shorts (bullish)" if rate > 0 else "🔴 Shorts pagam Longs (bearish)" if rate < 0 else "⚪ Neutro"
            return (
                f"📊 **Funding Rate para {ticker}** (via {result['exchange']}):\n\n"
                f"- **Taxa atual**: {rate:.4f}% (a cada 8h)\n"
                f"- **Taxa anualizada**: ~{abs(rate) * 3 * 365:.1f}%/ano\n"
                f"- **Direção**: {direction}\n"
                f"- **Mark Price**: {result['mark']}"
            )
    return f"⚠️ **Funding Rate indisponível** para {ticker} (todas as exchanges falharam)."


# ═══════════════════════════════════════════════════════════════════════════════
# Open Interest — multi-exchange with fallback
# ═══════════════════════════════════════════════════════════════════════════════

def _get_oi_binance(symbol: str) -> dict | None:
    data = _fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}", timeout=10)
    if isinstance(data, dict) and "openInterest" in data:
        return {"oi": float(data["openInterest"]), "exchange": "Binance"}
    return None


def _get_oi_bybit(symbol: str) -> dict | None:
    data = _fetch_json(f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol}&intervalTime=5min&limit=1", timeout=10)
    if isinstance(data, dict) and data.get("retCode") == 0:
        items = data.get("result", {}).get("list", [])
        if items:
            return {"oi": float(items[0].get("openInterest", 0)), "exchange": "Bybit"}
    return None


def _get_oi_okx(symbol: str) -> dict | None:
    data = _fetch_json(f"https://www.okx.com/api/v5/public/open-interest?instId={symbol}", timeout=10)
    if isinstance(data, dict) and data.get("code") == "0":
        items = data.get("data", [])
        if items:
            return {"oi": float(items[0].get("oi", 0)), "exchange": "OKX"}
    return None


_OI_FETCHERS = [_get_oi_binance, _get_oi_bybit, _get_oi_okx]


def get_open_interest(ticker: str) -> str:
    """Fetch open interest with multi-exchange fallback."""
    for exchange in ["binance", "bybit", "okx"]:
        symbol = _to_exchange_symbol(ticker, exchange)
        if not symbol:
            continue
        fetcher = _OI_FETCHERS[["binance", "bybit", "okx"].index(exchange)]
        result = fetcher(symbol)
        if result:
            return (
                f"📊 **Open Interest para {ticker}** (via {result['exchange']}):\n\n"
                f"- **OI Total**: {result['oi']:,.0f} contratos\n"
                f"- **Nota**: OI elevado + funding positivo = mercado alavancado long (risco de squeeze). "
                f"OI a cair = liquidações ou saída de capital."
            )
    return f"⚠️ **Open Interest indisponível** para {ticker} (todas as exchanges falharam)."


# ═══════════════════════════════════════════════════════════════════════════════
# Long/Short Ratio — multi-exchange with fallback
# ═══════════════════════════════════════════════════════════════════════════════

def _get_ls_ratio_binance(symbol: str) -> dict | None:
    data = _fetch_json(f"https://fapi.binance.com/fapi/v1/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1", timeout=10)
    if isinstance(data, list) and data:
        return {"ratio": float(data[0]["longShortRatio"]), "exchange": "Binance"}
    return None


def _get_ls_ratio_bybit(symbol: str) -> dict | None:
    data = _fetch_json(f"https://api.bybit.com/v5/market/account-ratio?category=linear&symbol={symbol}&period=5min&limit=1", timeout=10)
    if isinstance(data, dict) and data.get("retCode") == 0:
        items = data.get("result", {}).get("list", [])
        if items:
            ratio_str = items[0].get("buyRatio", "0.5")
            ratio = float(ratio_str)
            ls_ratio = ratio / (1 - ratio) if ratio < 1 else 999
            return {"ratio": round(ls_ratio, 2), "exchange": "Bybit"}
    return None


def _get_ls_ratio_okx(symbol: str) -> dict | None:
    data = _fetch_json(f"https://www.okx.com/api/v5/public/account-ratio?instId={symbol}&period=5m&limit=1", timeout=10)
    if isinstance(data, dict) and data.get("code") == "0":
        items = data.get("data", [])
        if items:
            ratio = float(items[0].get("buyRatio", "0.5"))
            ls_ratio = ratio / (1 - ratio) if ratio < 1 else 999
            return {"ratio": round(ls_ratio, 2), "exchange": "OKX"}
    return None


_LS_FETCHERS = [_get_ls_ratio_binance, _get_ls_ratio_bybit, _get_ls_ratio_okx]


def get_long_short_ratio(ticker: str) -> str:
    """Fetch long/short ratio with multi-exchange fallback."""
    for exchange in ["binance", "bybit", "okx"]:
        symbol = _to_exchange_symbol(ticker, exchange)
        if not symbol:
            continue
        fetcher = _LS_FETCHERS[["binance", "bybit", "okx"].index(exchange)]
        result = fetcher(symbol)
        if result:
            ratio = result["ratio"]
            long_pct = (ratio / (1 + ratio)) * 100
            short_pct = 100 - long_pct
            if long_pct > 70:
                signal = "🔴 Maioria esmagadora long — risco extremo de liquidação em cascata"
            elif long_pct > 60:
                signal = "🟠 Maioria long — sentimento positivo mas atenção a reversões"
            elif long_pct > 50:
                signal = "🟢 Ligeira maioria long — saudável"
            elif long_pct < 30:
                signal = "🟢 Maioria esmagadora short — potencial short squeeze"
            elif long_pct < 40:
                signal = "🟠 Maioria short — sentimento negativo"
            else:
                signal = "⚪ Equilibrado"
            return (
                f"📊 **Rácio Long/Short para {ticker}** (via {result['exchange']}):\n\n"
                f"- **Long/Short Ratio**: {ratio:.2f}\n"
                f"- **Long**: {long_pct:.1f}% | **Short**: {short_pct:.1f}%\n"
                f"- **Sinal**: {signal}"
            )
    return f"⚠️ **Rácio Long/Short indisponível** para {ticker} (todas as exchanges falharam)."


# ═══════════════════════════════════════════════════════════════════════════════
# CoinGecko — Market data (dominance, market cap, sentiment)
# ═══════════════════════════════════════════════════════════════════════════════

def get_coingecko_market_data(ticker: str) -> str:
    """Fetch market data from CoinGecko free API.

    Returns global market stats (BTC dominance, total market cap, fear & greed)
    plus coin-specific data (market cap rank, price change %, ATH distance).
    """
    cg_id = _COINGECKO_IDS.get(ticker)

    # Global data (always available)
    global_data = _fetch_json("https://api.coingecko.com/api/v3/global", timeout=15)
    parts = []

    if isinstance(global_data, dict) and "data" in global_data:
        gd = global_data["data"]
        btc_dom = gd.get("market_cap_percentage", {}).get("btc", "N/A")
        eth_dom = gd.get("market_cap_percentage", {}).get("eth", "N/A")
        total_mcap = gd.get("total_market_cap", {}).get("usd", 0)
        volume_24h = gd.get("total_volume", {}).get("usd", 0)
        mcap_change = gd.get("market_cap_change_percentage_24h_usd", 0)

        parts.append("🌍 **Dados Globais do Mercado Cripto** (via CoinGecko):\n")
        parts.append(f"- **Market Cap Total**: ${total_mcap:,.0f}")
        parts.append(f"- **Dominância BTC**: {btc_dom}% | **ETH**: {eth_dom}%")
        parts.append(f"- **Volume 24h**: ${volume_24h:,.0f}")
        parts.append(f"- **Variação 24h do MCap**: {mcap_change:+.1f}%")
        parts.append("")

    # Coin-specific data
    if cg_id:
        coin_data = _fetch_json(
            f"https://api.coingecko.com/api/v3/coins/{cg_id}"
            "?localization=false&tickers=false&community_data=false&developer_data=false",
            timeout=15,
        )
        if isinstance(coin_data, dict) and "market_data" in coin_data:
            md = coin_data["market_data"]
            rank = md.get("market_cap_rank", "N/A")
            price_change_24h = md.get("price_change_percentage_24h", 0)
            price_change_7d = md.get("price_change_percentage_7d", 0)
            price_change_30d = md.get("price_change_percentage_30d", 0)
            ath = md.get("ath", {}).get("usd", 0)
            ath_pct = md.get("ath_change_percentage", {}).get("usd", 0)
            current_price = md.get("current_price", {}).get("usd", 0)

            parts.append(f"📈 **Dados de Mercado: {ticker}** (via CoinGecko):\n")
            parts.append(f"- **Market Cap Rank**: #{rank}")
            parts.append(f"- **Preço Atual**: ${current_price:,.2f}")
            parts.append(f"- **ATH**: ${ath:,.2f} ({ath_pct:+.1f}% desde ATH)")
            parts.append(f"- **Variação 24h**: {price_change_24h:+.1f}%")
            parts.append(f"- **Variação 7d**: {price_change_7d:+.1f}%")
            parts.append(f"- **Variação 30d**: {price_change_30d:+.1f}%")

    if parts:
        return "\n".join(parts)
    return f"⚠️ Dados CoinGecko indisponíveis para {ticker}."


# ═══════════════════════════════════════════════════════════════════════════════
# Blockchain.com — BTC network data
# ═══════════════════════════════════════════════════════════════════════════════

def get_btc_network_data(ticker: str) -> str:
    """Fetch BTC network data from mempool.space API.

    Only returns data for BTC-USD. Includes hashrate, mempool info,
    transaction fees, and block height.
    """
    if ticker != "BTC-USD":
        return ""

    parts = ["⛓️ **Rede Bitcoin** (via mempool.space):\n"]

    # Mempool stats
    mempool = _fetch_json("https://mempool.space/api/v1/fees/mempool-blocks", timeout=10)
    if isinstance(mempool, list) and mempool:
        # mempool-blocks returns fee ranges for blocks in the mempool
        num_blocks = len(mempool)
        if num_blocks > 0:
            fee_range = mempool[0].get("feeRange", [0, 0])
            min_fee = fee_range[0] if len(fee_range) > 0 else 0
            max_fee = fee_range[-1] if len(fee_range) > 1 else 0

            congestion = (
                "🚨 Muito congestionado" if num_blocks > 20
                else "⚠️ Congestionado" if num_blocks > 10
                else "🟢 Normal" if num_blocks < 5
                else "🟡 Moderado"
            )
            parts.append(f"- **Blocos no Mempool**: {num_blocks} ({congestion})")
            parts.append(f"- **Taxa mínima (próx. bloco)**: {min_fee:.0f} sat/vB")
            if max_fee > 0:
                parts.append(f"- **Taxa máxima**: {max_fee:.0f} sat/vB")

    # Recommended fees
    fees = _fetch_json("https://mempool.space/api/v1/fees/recommended", timeout=10)
    if isinstance(fees, dict):
        fastest = fees.get("fastestFee", "N/A")
        half_hour = fees.get("halfHourFee", "N/A")
        hour = fees.get("hourFee", "N/A")
        parts.append(f"- **Taxa recomendada**: {half_hour} sat/vB (30min) | {fastest} (rápido) | {hour} (1h)")

    # Current block height
    tip = _fetch_json("https://mempool.space/api/blocks/tip/height", timeout=10)
    if isinstance(tip, int):
        parts.append(f"- **Bloco atual**: #{tip:,}")

    # Hashrate (via blocks endpoint)
    hashrate_data = _fetch_json("https://mempool.space/api/v1/mining/hashrate/1w", timeout=10)
    if isinstance(hashrate_data, dict):
        current_hashrate = hashrate_data.get("currentHashrate", 0)
        if current_hashrate:
            parts.append(f"- **Hashrate (7d)**: {current_hashrate / 1e18:.1f} EH/s")

    if len(parts) == 1:
        return ""  # No data available — silently skip

    parts.append("")
    parts.append("**Interpretação:** Mempool congestionado = taxas elevadas e actividade na rede. "
                  "Hashrate a subir = confiança dos mineiros. Taxas baixas = rede saudável.")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregated summary — injects into graph state
# ═══════════════════════════════════════════════════════════════════════════════

def get_crypto_onchain_summary(ticker: str) -> str:
    """Aggregate ALL crypto data sources into one markdown block.

    Called by TradingAgentsGraph when asset_type='crypto'.
    Multi-exchange derivatives + CoinGecko market + BTC network (if applicable).
    """
    if not ticker.endswith("-USD"):
        return ""

    parts = [f"## 📊 Dados Cripto para {ticker}\n"]

    # Derivatives (multi-exchange fallback)
    funding = get_funding_rate(ticker)
    if "indisponível" not in funding.lower():
        parts.append(funding)
        parts.append("")

    oi = get_open_interest(ticker)
    if "indisponível" not in oi.lower():
        parts.append(oi)
        parts.append("")

    ls_data = get_long_short_ratio(ticker)
    if "indisponível" not in ls_data.lower():
        parts.append(ls_data)
        parts.append("")

    # Market data (CoinGecko)
    cg = get_coingecko_market_data(ticker)
    if "indisponível" not in cg.lower() or "🌍" in cg:
        parts.append(cg)
        parts.append("")

    # BTC network data
    btc_net = get_btc_network_data(ticker)
    if btc_net:
        parts.append(btc_net)
        parts.append("")

    if len(parts) == 1:
        return f"⚠️ Dados cripto indisponíveis para {ticker} (todas as fontes falharam).\n"

    # Interpretation guide
    parts.append(
        "---\n"
        "**🧠 Guia de Interpretação para Trading:**\n"
        "- **Funding positivo extremo (>0.05%) + OI em máximos + maioria long** = "
        "⚠️ Perigo de liquidação em cascata se o preço cair. Cautela em longs.\n"
        "- **Funding negativo extremo (<-0.03%) + OI elevado + maioria short** = "
        "⚠️ Potencial short squeeze. Cautela em shorts.\n"
        "- **OI a cair -20%+ em 24h** = Saída de capital → fraqueza da tendência.\n"
        "- **Dominância BTC a subir + alts a cair** = Rotação para segurança (risk-off).\n"
        "- **Dominância BTC a cair + alts a subir** = Risk-on, 'alt season'.\n"
        "- **Hashrate a cair significativamente** = Possível capitulação de mineiros.\n"
        "- **Mempool congestionado** = Taxas altas, pode impactar utilizadores/exchanges.\n"
        "- **Funding neutro + OI estável + L/S equilibrado** = Mercado saudável, sem extremos."
    )

    return "\n".join(parts)
