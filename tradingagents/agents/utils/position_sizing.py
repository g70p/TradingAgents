"""Position sizing utilities for TradingAgents.

Provides ATR-based and Kelly Criterion position sizing calculations
for integration into the trader and portfolio manager agents.
"""

from __future__ import annotations

import logging
import math
from decimal import ROUND_FLOOR, Decimal
from typing import Any

logger = logging.getLogger(__name__)


def calculate_atr(
    high_prices: list[float],
    low_prices: list[float],
    close_prices: list[float],
    period: int = 14,
) -> float | None:
    """Calculate Average True Range (ATR) for a series of OHLC data.

    Args:
        high_prices: List of period highs (most recent last)
        low_prices: List of period lows (most recent last)
        close_prices: List of period closes (most recent last)
        period: ATR lookback period (default 14)

    Returns:
        ATR value, or None if insufficient data
    """
    if period < 1 or not (len(high_prices) == len(low_prices) == len(close_prices)):
        return None
    if any(not math.isfinite(x) or x <= 0 for series in (high_prices, low_prices, close_prices) for x in series):
        return None
    if any(high < low for high, low in zip(high_prices, low_prices, strict=True)):
        return None
    if len(high_prices) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(high_prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = close_prices[i - 1]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    # Use the most recent `period` true ranges
    recent_tr = true_ranges[-period:]
    return sum(recent_tr) / period


def calculate_atr_position_size(
    *, account_balance: float, risk_percent: float = 1.0,
    atr_value: float, current_price: float, atr_multiplier: float = 2.0,
    min_position: float = 0.0, max_position_percent: float = 25.0,
    unit_step: float = 1.0, side: str = "long",
) -> dict[str, Any]:
    """Return quantity, monetary exposure and actual nominal stop risk separately.

    risk / stop_distance gives UNITS; units * price gives monetary position_size.
    The stop risk excludes fees, gaps and slippage. Quantity is rounded down.
    """
    values = (account_balance, risk_percent, atr_value, current_price,
              atr_multiplier, max_position_percent, unit_step)
    if (any(not math.isfinite(v) or v <= 0 for v in values)
            or not math.isfinite(min_position) or min_position < 0
            or risk_percent > 100 or max_position_percent > 100
            or side not in {"long", "short"}):
        raise ValueError("Invalid sizing parameters")
    stop_distance = atr_value * atr_multiplier
    stop_loss_price = current_price + (-stop_distance if side == "long" else stop_distance)
    if stop_loss_price <= 0:
        raise ValueError("The stop price must be positive")
    risk_budget = account_balance * risk_percent / 100
    exposure_cap = account_balance * max_position_percent / 100
    raw_units = min(risk_budget / stop_distance, exposure_cap / current_price)
    step = Decimal(str(unit_step))
    units = float((Decimal(str(raw_units)) / step).to_integral_value(rounding=ROUND_FLOOR) * step)
    position_size = units * current_price
    if position_size < min_position:
        units = position_size = 0.0
    risk_amount = units * stop_distance
    return {
        "position_size": round(position_size, 8), "units": units,
        "stop_loss_price": round(stop_loss_price, 8),
        "risk_amount": round(risk_amount, 8), "risk_budget": round(risk_budget, 8),
        "atr_value": round(atr_value, 6), "atr_multiplier": atr_multiplier,
        "side": side,
        "note": (f"Exposição={position_size:.2f}; risco nominal ao stop={risk_amount:.2f} "
                 f"(orçamento={risk_budget:.2f}). Exclui custos, gaps e slippage."),
    }


def calculate_kelly_fraction(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    max_fraction: float = 0.25,
) -> dict[str, Any]:
    """Calculate Kelly Criterion fraction for position sizing.

    Kelly formula: f* = W - ((1 - W) / R)
    where W = win rate, R = avg_win / avg_loss (reward-to-risk ratio)

    Uses half-Kelly by default for conservative sizing.

    Args:
        win_rate: Historical win rate (0.0 to 1.0)
        avg_win: Average winning trade return (positive)
        avg_loss: Average losing trade return (positive, e.g. 0.02 for 2%)
        max_fraction: Maximum allowed fraction (cap for safety)

    Returns:
        Dict with kelly_fraction, half_kelly, recommended_fraction, and note
    """
    from tradingagents.dataflows.math_tools import kelly_fraction

    result = kelly_fraction(win_rate, avg_win, avg_loss, max_fraction)
    if "error" in result:
        return {"error": result["error"], "note": "Dimensionamento Kelly indisponível."}
    return {
        "kelly_fraction": result["full_fraction"],
        "half_kelly": result["half_fraction"],
        "recommended_fraction": result["half_fraction"],
        "fraction_basis": result["fraction_basis"],
        "note": result["interpretation"],
    }


def generate_atr_sizing_guidance(
    ticker: str,
    current_price: float,
    highs: list[float],
    lows: list[float],
    closes: list[float],
    account_balance: float = 10_000,
    risk_percent: float = 1.0,
    atr_period: int = 14,
    atr_multiplier: float = 2.0,
    unit_step: float = 1.0,
    side: str = "long",
) -> str:
    """Generate a human-readable ATR-based position sizing recommendation.

    Args:
        ticker: Instrument ticker
        current_price: Latest closing price
        highs: Recent period highs
        lows: Recent period lows
        closes: Recent period closes
        account_balance: Account balance in quote currency
        risk_percent: Risk percentage per trade
        atr_period: ATR lookback period
        atr_multiplier: Stop-loss multiplier

    Returns:
        Markdown-formatted sizing guidance string
    """
    atr = calculate_atr(highs, lows, closes, period=atr_period)

    if atr is None:
        return (
            f"⚠️ **Dimensionamento ATR indisponível para {ticker}**: "
            f"dados insuficientes (< {atr_period + 1} candles). "
            "Dimensionamento indisponível; não foi calculada uma posição."
        )

    sizing = calculate_atr_position_size(
        account_balance=account_balance,
        risk_percent=risk_percent,
        atr_value=atr,
        current_price=current_price,
        atr_multiplier=atr_multiplier,
        unit_step=unit_step, side=side,
    )

    vol_pct = (atr / current_price) * 100 if current_price > 0 else 0

    return (
        f"📊 **Dimensionamento de Posição baseado em ATR para {ticker}:**\n\n"
        f"- **ATR({atr_period})**: {atr:.4f} ({vol_pct:.2f}% do preço)\n"
        f"- **Preço Atual**: {current_price:.4f}\n"
        f"- **Stop-Loss sugerido**: {sizing['stop_loss_price']:.4f} "
        f"(distância: {atr * atr_multiplier:.4f} = {atr_multiplier}x ATR)\n"
        f"- **Orçamento de risco**: {risk_percent:.1f}% = {sizing['risk_budget']:.2f}\n"
        f"- **Risco nominal da posição**: {sizing['risk_amount']:.2f}\n"
        f"- **Tamanho da posição**: {sizing['position_size']:.2f} "
        f"({sizing['units']} unidades)\n"
        f"- **Nota**: {sizing['note']}"
    )
