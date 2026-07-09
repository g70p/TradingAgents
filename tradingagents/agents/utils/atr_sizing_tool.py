"""ATR-based position sizing tool for the trader agent.

This tool is bound to the trader's LLM so it can compute position sizing
with real volatility data rather than guessing.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import yfinance as yf
from langchain_core.tools import tool

from tradingagents.agents.utils.position_sizing import generate_atr_sizing_guidance
from tradingagents.dataflows.symbol_utils import normalize_symbol


@tool
def get_atr_position_sizing(
    ticker: str,
    current_date: str,
    account_balance: float = 10_000,
    risk_percent: float = 1.0,
    atr_multiplier: float = 2.0,
    lookback_days: int = 30,
) -> str:
    """Calculate ATR-based position sizing for a ticker.

    Fetches recent OHLCV data from Yahoo Finance, computes ATR(14),
    and returns sizing guidance including suggested stop-loss and
    position size based on the configured risk percentage.

    Args:
        ticker: The ticker symbol (e.g., 'BTC-USD', 'NVDA')
        current_date: The trade date in 'YYYY-MM-DD' format
        account_balance: Total account balance in quote currency (default 10000)
        risk_percent: Percentage of account to risk per trade (default 1.0)
        atr_multiplier: Stop-loss distance as ATR multiplier (default 2.0)
        lookback_days: Days of historical data to fetch (default 30)

    Returns:
        Markdown-formatted position sizing recommendation
    """
    try:
        trade_date = datetime.strptime(current_date, "%Y-%m-%d")
        start = trade_date - timedelta(days=lookback_days + 7)  # buffer
        end = trade_date + timedelta(days=1)

        normalized = normalize_symbol(ticker)
        data = yf.Ticker(normalized).history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

        if len(data) < 15:
            return f"⚠️ Dados insuficientes para {ticker}: apenas {len(data)} candles disponíveis (mínimo 15 para ATR(14))."

        # Use data up to the trade date
        data = data[data.index <= trade_date + timedelta(days=1)]
        if len(data) < 15:
            return f"⚠️ Dados insuficientes até à data {current_date} para {ticker}."

        highs = data["High"].tolist()
        lows = data["Low"].tolist()
        closes = data["Close"].tolist()
        current_price = closes[-1]

        return generate_atr_sizing_guidance(
            ticker=ticker,
            current_price=current_price,
            highs=highs,
            lows=lows,
            closes=closes,
            account_balance=account_balance,
            risk_percent=risk_percent,
            atr_multiplier=atr_multiplier,
        )

    except Exception as e:
        return f"⚠️ Erro ao calcular dimensionamento ATR para {ticker}: {e}"
