"""LangChain tools wrapping the G70P math engine for the Math Analyst agent."""
from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.math_tools import (
    detect_regime,
    expected_price_range,
    implied_metrics,
    kelly_fraction,
    tail_exponent,
)


@tool
def get_expected_price_range(
    ticker: Annotated[str, "Ticker symbol (e.g. BCP.LS, BTC-USD)"],
    closes_json: Annotated[str, "JSON array of closing prices"],
    lookback_days: Annotated[int, "Number of days for vol calculation"] = 20,
    projection_days: Annotated[int, "Days to project forward"] = 5,
    confidence: Annotated[float, "Confidence level (0.68 = 1σ, 0.95 = 2σ)"] = 0.68,
) -> str:
    """Bâchelier (1900): Expected price range via Brownian motion.

    Uses recent volatility to project a confidence cone for where the
    price is likely to be in `projection_days` trading days.

    Returns expected upper/lower bounds. Higher confidence = wider cone.
    """
    import json
    closes = json.loads(closes_json)
    result = expected_price_range(closes, lookback_days, projection_days, confidence)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@tool
def get_tail_risk(
    returns_json: Annotated[str, "JSON array of daily log-returns"],
) -> str:
    """Mandelbrot (1963): Power-law tail exponent analysis.

    Estimates the tail exponent α from a series of returns.
    α < 2 → infinite variance (extreme outlier risk).
    α ≈ 3+ → closer to Gaussian (safer).

    Returns α value and risk assessment.
    """
    import json
    returns = json.loads(returns_json)
    result = tail_exponent(returns)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@tool
def get_regime_detection(
    closes_json: Annotated[str, "JSON array of closing prices (100+ recommended)"],
    volumes_json: Annotated[str, "Optional JSON array of volumes"] = "",
) -> str:
    """Baum (1960s): Hidden Markov Model regime detection.

    Detects latent market regimes from price data:
    - Regime 0: sideways / mean-reverting
    - Regime 1: bull trending
    - Regime 2: bear / high-vol

    Returns current regime, confidence, and per-regime statistics.
    """
    import json
    closes = json.loads(closes_json)
    volumes = json.loads(volumes_json) if volumes_json else None
    result = detect_regime(closes, volumes)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@tool
def get_kelly_sizing(
    win_rate: Annotated[float, "Win rate as decimal (0.0-1.0)"],
    avg_win_pct: Annotated[float, "Average win as percentage (e.g. 2.5 for 2.5%)"],
    avg_loss_pct: Annotated[float, "Average loss as percentage (e.g. 1.0 for 1.0%)"],
) -> str:
    """Ed Thorp: Kelly Criterion optimal position sizing.

    Computes the optimal fraction of capital to risk per trade.
    Use Half-Kelly (50% of the result) for real trading.

    Returns full Kelly, Half-Kelly, and risk verdict.
    """
    import json
    result = kelly_fraction(win_rate, avg_win_pct, avg_loss_pct)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@tool
def get_implied_volatility(
    spot: Annotated[float, "Current spot price"],
    strike: Annotated[float, "Option strike price"],
    days_to_expiry: Annotated[int, "Days to option expiry"],
    option_price: Annotated[float, "Market price of the option"],
    is_call: Annotated[bool, "True for call, False for put"] = True,
) -> str:
    """Black-Scholes-Merton (1973): Implied volatility and Greeks.

    Computes implied volatility, delta, gamma, and ITM probability
    from an option's market price.
    """
    import json
    result = implied_metrics(spot, strike, days_to_expiry, option_price, is_call)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)
