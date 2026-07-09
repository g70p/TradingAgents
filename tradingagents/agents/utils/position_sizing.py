"""Position sizing utilities for TradingAgents.

Provides ATR-based and Kelly Criterion position sizing calculations
for integration into the trader and portfolio manager agents.
"""

from __future__ import annotations

import logging
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
    *,
    account_balance: float,
    risk_percent: float = 1.0,
    atr_value: float,
    current_price: float,
    atr_multiplier: float = 2.0,
    min_position: float = 0.0,
    max_position_percent: float = 25.0,
) -> dict[str, Any]:
    """Calculate position size based on ATR volatility.

    Uses the formula: position_size = (account * risk_pct) / (ATR * multiplier)

    This ensures the stop-loss distance (ATR * multiplier) only risks the
    configured percentage of the account.

    Args:
        account_balance: Total account balance in quote currency
        risk_percent: Percentage of account to risk per trade (default 1%)
        atr_value: Current ATR(14) value
        current_price: Current instrument price
        atr_multiplier: Stop-loss distance multiplier (default 2x ATR)
        min_position: Minimum position size (for filtering noise)
        max_position_percent: Maximum position size as % of account

    Returns:
        Dict with position_size, units, stop_loss_price, risk_amount, and note
    """
    if atr_value <= 0 or current_price <= 0:
        return {
            "position_size": 0.0,
            "units": 0,
            "stop_loss_price": 0.0,
            "risk_amount": 0.0,
            "note": "Dados de ATR ou preço inválidos — não é possível calcular o dimensionamento.",
        }

    risk_amount = account_balance * (risk_percent / 100.0)
    stop_distance = atr_value * atr_multiplier
    position_size = risk_amount / stop_distance if stop_distance > 0 else 0.0
    units = int(position_size / current_price) if current_price > 0 else 0

    # Apply position limits
    max_position_value = account_balance * (max_position_percent / 100.0)
    if position_size > max_position_value:
        position_size = max_position_value
        units = int(max_position_value / current_price)
        note = (
            f"Posição limitada a {max_position_percent:.0f}% da conta "
            f"({max_position_value:.2f}). ATR={atr_value:.4f}, "
            f"Stop a {atr_multiplier}x ATR={stop_distance:.4f}."
        )
    elif position_size < min_position and min_position > 0:
        note = (
            f"Tamanho de posição ({position_size:.2f}) abaixo do mínimo "
            f"({min_position:.2f}). Considera não entrar."
        )
    else:
        note = (
            f"ATR={atr_value:.4f}, Stop a {atr_multiplier}x ATR={stop_distance:.4f}, "
            f"Risco={risk_percent:.1f}% da conta ({risk_amount:.2f})."
        )

    stop_loss_price = round(current_price - stop_distance, 8)

    return {
        "position_size": round(position_size, 2),
        "units": units,
        "stop_loss_price": stop_loss_price,
        "risk_amount": round(risk_amount, 2),
        "atr_value": round(atr_value, 6),
        "atr_multiplier": atr_multiplier,
        "note": note,
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
    if win_rate <= 0 or avg_loss <= 0 or avg_win <= 0:
        return {
            "kelly_fraction": 0.0,
            "half_kelly": 0.0,
            "recommended_fraction": 0.0,
            "note": "Dados insuficientes para calcular o Kelly Criterion.",
        }

    reward_risk_ratio = avg_win / avg_loss
    kelly = win_rate - ((1 - win_rate) / reward_risk_ratio)
    kelly = max(0.0, min(kelly, max_fraction))
    half_kelly = kelly / 2.0

    return {
        "kelly_fraction": round(kelly, 4),
        "half_kelly": round(half_kelly, 4),
        "recommended_fraction": round(half_kelly, 4),
        "note": (
            f"Kelly={kelly:.1%}, Meio-Kelly={half_kelly:.1%} "
            f"(W={win_rate:.1%}, R={reward_risk_ratio:.1f}:1)."
        ),
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
            f"Usa uma abordagem conservadora de 1-2% do portfólio."
        )

    sizing = calculate_atr_position_size(
        account_balance=account_balance,
        risk_percent=risk_percent,
        atr_value=atr,
        current_price=current_price,
        atr_multiplier=atr_multiplier,
    )

    vol_pct = (atr / current_price) * 100 if current_price > 0 else 0

    return (
        f"📊 **Dimensionamento de Posição baseado em ATR para {ticker}:**\n\n"
        f"- **ATR({atr_period})**: {atr:.4f} ({vol_pct:.2f}% do preço)\n"
        f"- **Preço Atual**: {current_price:.4f}\n"
        f"- **Stop-Loss sugerido**: {sizing['stop_loss_price']:.4f} "
        f"(distância: {atr * atr_multiplier:.4f} = {atr_multiplier}x ATR)\n"
        f"- **Risco por trade**: {risk_percent:.1f}% = {sizing['risk_amount']:.2f}\n"
        f"- **Tamanho da posição**: {sizing['position_size']:.2f} "
        f"({sizing['units']} unidades)\n"
        f"- **Nota**: {sizing['note']}"
    )
