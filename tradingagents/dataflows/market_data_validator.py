"""Deterministic market-data verification snapshot.

The market analyst is an LLM that can confabulate exact numbers — citing a
Bollinger band or a "historically validated bounce" that the underlying data
doesn't support (#830). This module computes a ground-truth snapshot (latest
OHLCV row on or before the analysis date, common indicators, recent closes)
the analyst is told to treat as the source of truth for any exact numeric
claim. Deterministic, no LLM involved.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from stockstats import wrap

from tradingagents.dataflows.stockstats_utils import load_ohlcv

# A fixed, common indicator set so the snapshot is the same shape every run.
DEFAULT_SNAPSHOT_INDICATORS: tuple[str, ...] = (
    "close_10_ema", "close_50_sma", "close_200_sma",
    "rsi", "boll", "boll_ub", "boll_lb",
    "macd", "macds", "macdh", "atr",
)


def _verified_rows(symbol: str, curr_date: str) -> pd.DataFrame:
    """OHLCV on or before curr_date, date-sorted. Raises if nothing usable.

    ``load_ohlcv`` already normalizes the Date column and filters out
    look-ahead rows, but we re-apply the cutoff defensively — this is a
    verification path, so it must not trust its input to be pre-filtered.
    """
    data = load_ohlcv(symbol, curr_date)
    if data is None or data.empty:
        raise ValueError(f"No OHLCV data available for {symbol}.")

    df = data.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df[df["Date"] <= pd.to_datetime(curr_date)].sort_values("Date")
    if df.empty:
        raise ValueError(f"No OHLCV rows on or before {curr_date} for {symbol}.")
    return df


def _fmt(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def build_verified_market_snapshot(
    symbol: str,
    curr_date: str,
    look_back_days: int = 30,
    indicators: Iterable[str] | None = None,
) -> str:
    """Render a ground-truth snapshot: latest OHLCV row, indicators, recent closes."""
    # `df` keeps the original capitalized OHLCV columns (Open/High/Low/Close/
    # Volume); stockstats `wrap()` lowercases columns and adds indicator
    # columns, so read raw prices from `df` and indicators from `stock_df`.
    df = _verified_rows(symbol, curr_date)
    stock_df = wrap(df.copy())

    selected = tuple(indicators or DEFAULT_SNAPSHOT_INDICATORS)
    indicator_values: dict[str, str] = {}
    for name in selected:
        try:
            stock_df[name]  # triggers stockstats calculation
            indicator_values[name] = _fmt(stock_df.iloc[-1][name])
        except Exception as exc:  # noqa: BLE001 — one bad indicator shouldn't sink the snapshot
            indicator_values[name] = f"N/A ({type(exc).__name__})"

    latest = df.iloc[-1]
    latest_date = _fmt(latest["Date"])
    window = max(1, min(int(look_back_days), 30))
    recent = df.tail(window)

    lines = [
        f"## Verified market data snapshot for {symbol.upper()}",
        "",
        f"- Requested analysis date: {curr_date}",
        f"- Latest trading row used: {latest_date}",
        "- Rows after the requested analysis date are excluded before verification.",
        "",
        "### Latest verified OHLCV row",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for field in ("Open", "High", "Low", "Close", "Volume"):
        lines.append(f"| {field} | {_fmt(latest.get(field))} |")

    lines += ["", "### Verified technical indicators (latest row)", "",
              "| Indicator | Value |", "|---|---:|"]
    for name, value in indicator_values.items():
        lines.append(f"| {name} | {value} |")

    lines += ["", f"### Recent verified closes (last {len(recent)} rows)", "",
              "| Date | Close |", "|---|---:|"]
    for _, row in recent.iterrows():
        lines.append(f"| {_fmt(row['Date'])} | {_fmt(row.get('Close'))} |")

    lines += [
        "",
        "### Volume & Volatilidade (instantâneo vs histórico)",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
    ]

    # ── Volume relativo ──────────────────────────────────────────
    vol_window = min(20, len(df) - 1)
    if vol_window > 0 and "Volume" in df.columns:
        today_vol = latest.get("Volume")
        avg_vol = df["Volume"].iloc[-(vol_window + 1):-1].mean()
        if pd.notna(today_vol) and pd.notna(avg_vol) and avg_vol > 0:
            vol_ratio = today_vol / avg_vol
            lines.append(f"| Volume (hoje) | {_fmt(today_vol)} |")
            lines.append(f"| Volume médio ({vol_window}d) | {_fmt(avg_vol)} |")
            lines.append(f"| Volume relativo | {vol_ratio:.2f}x {'🔴 ALTO' if vol_ratio > 1.5 else '🟢 NORMAL' if vol_ratio > 0.5 else '🟡 BAIXO'} |")
        else:
            lines.append("| Volume relativo | N/A (dados insuficientes) |")
    else:
        lines.append("| Volume relativo | N/A (dados insuficientes) |")

    # ── Volatilidade relativa ────────────────────────────────────
    tr_window = min(20, len(df) - 1)
    if tr_window > 0 and all(c in df.columns for c in ("High", "Low", "Close")):
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)
        if len(true_ranges) > tr_window:
            today_tr = true_ranges[-1]
            avg_tr = sum(true_ranges[-(tr_window + 1):-1]) / tr_window
            if avg_tr > 0:
                vr = today_tr / avg_tr
                lines.append(f"| True Range (hoje) | {_fmt(today_tr)} |")
                lines.append(f"| True Range médio ({tr_window}d) | {_fmt(avg_tr)} |")
                lines.append(f"| Volatilidade relativa | {vr:.2f}x {'🔴 ALTA' if vr > 1.5 else '🟢 NORMAL' if vr > 0.5 else '🟡 BAIXA'} |")
            else:
                lines.append("| Volatilidade relativa | N/A (média zero) |")
        else:
            lines.append("| Volatilidade relativa | N/A (dados insuficientes) |")
    else:
        lines.append("| Volatilidade relativa | N/A (dados insuficientes) |")

    lines += [
        "",
        "Use this snapshot as the source of truth for exact OHLCV, price-level, "
        "and indicator-value claims. If another tool output conflicts with it, "
        "flag the discrepancy rather than inventing a reconciled number. Do not "
        "claim historical validation, support/resistance bounces, or exact "
        "percentage moves unless directly supported by tool output with concrete "
        "dates and prices.",
    ]
    return "\n".join(lines)
