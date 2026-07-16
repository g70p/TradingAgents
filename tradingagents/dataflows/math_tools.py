"""
G70P Math Agent Tools — deterministic quantitative analysis.
Zero LLM hallucination risk: the LLM only CALLS these tools;
all computation is pure Python/NumPy/SciPy.

Authors/Concepts:
  Bachelier (1900) — Brownian price diffusion, expected range cone
  Mandelbrot (1960s) — Power-law tail exponents, fat-tail risk
  Baum (1960s) — Hidden Markov Model regime detection
  Ed Thorp (1960s) — Kelly Criterion optimal position sizing
  Black-Scholes-Merton (1973) — options-implied probabilities
"""
from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Bächelier — Expected price range via Brownian diffusion
# ═══════════════════════════════════════════════════════════════

def expected_price_range(
    closes: list[float],
    lookback_days: int = 20,
    projection_days: int = 5,
    confidence: float = 0.68,
) -> dict[str, Any]:
    """
    Bâchelier (1900): price follows Brownian motion.
    Compute volatility from recent prices, then project a
    confidence cone ``projection_days`` into the future.

    Returns expected upper/lower bounds at the given confidence
    level (1σ ≈ 68%, 2σ ≈ 95%).
    """
    if len(closes) < max(lookback_days, 5):
        return {"error": f"Need at least {max(lookback_days, 5)} data points"}
    try:
        recent = np.array(closes[-lookback_days:], dtype=np.float64)
        log_returns = np.diff(np.log(recent))
        # Annualize
        daily_vol = float(np.std(log_returns, ddof=1))
        if daily_vol <= 0:
            return {"error": "Zero volatility — price is flat"}
        annual_vol = daily_vol * math.sqrt(252)

        latest = float(recent[-1])
        z_score = float(np.abs(np.percentile(np.random.standard_normal(100000),
                                              confidence * 100)))
        drift = float(np.mean(log_returns)) * projection_days
        half_width = z_score * daily_vol * math.sqrt(projection_days)

        upper = latest * math.exp(drift + half_width)
        lower = latest * math.exp(drift - half_width)

        return {
            "latest_price": round(latest, 2),
            "annual_vol_pct": round(annual_vol * 100, 1),
            "daily_vol_pct": round(daily_vol * 100, 3),
            "confidence_pct": int(confidence * 100),
            "projection_days": projection_days,
            "expected_upper": round(upper, 2),
            "expected_lower": round(lower, 2),
            "range_width_pct": round((upper - lower) / latest * 100, 1),
            "interpretation": (
                f"Com {int(confidence*100)}% de confiança, o preço deve "
                f"ficar entre {lower:.2f} e {upper:.2f} nos próximos "
                f"{projection_days} dias. Faixa de {((upper-lower)/latest*100):.1f}%."
            ),
        }
    except Exception as exc:
        logger.warning("Bachelier range failed: %s", exc)
        return {"error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# Mandelbrot — Power-law tail exponent (α)
# ═══════════════════════════════════════════════════════════════

def tail_exponent(
    returns: list[float],
    min_data: int = 60,
) -> dict[str, Any]:
    """
    Mandelbrot (1963): financial returns follow power-law (α-stable)
    distributions with heavy tails. Estimate the tail exponent α.

    α < 2 → infinite variance (extreme risk)
    α < 3 → infinite skewness
    α → higher → thinner tails (closer to Gaussian)

    Uses Hill estimator on the upper tail (largest 10% of absolute returns).
    """
    if len(returns) < min_data:
        return {"error": f"Need at least {min_data} return observations"}
    try:
        rets = np.array([abs(r) for r in returns], dtype=np.float64)
        if np.all(rets == 0):
            return {"error": "All returns are zero"}

        # Use top 10% for tail estimation
        k = max(10, int(len(rets) * 0.10))
        sorted_rets = np.sort(rets)
        tail = sorted_rets[-k:]
        threshold = sorted_rets[-k]

        # Hill estimator: α = k / Σ ln(x_i / threshold)
        log_ratio = np.log(tail / threshold)
        sum_log = float(np.sum(log_ratio))
        alpha = k / sum_log if sum_log > 0 else float("inf")

        # Qualitative assessment
        if alpha <= 2:
            risk_level = "CRÍTICO — variância infinita, outliers são a regra"
        elif alpha <= 3:
            risk_level = "ALTO — cauda gorda, skewness infinita"
        elif alpha <= 4:
            risk_level = "MODERADO — cauda mais gorda que Gaussiana"
        else:
            risk_level = "BAIXO — próximo de Gaussian"

        return {
            "tail_exponent_alpha": round(alpha, 2),
            "tail_samples": k,
            "tail_threshold": round(float(threshold), 6),
            "risk_assessment": risk_level,
            "note": (
                "Mandelbrot: α < 2 = variância infinita. "
                "α = 2.0 é Gaussian; α ↓ significa mais risco de outlier."
            ),
            "interpretation": f"α={alpha:.2f} → {risk_level}",
        }
    except Exception as exc:
        logger.warning("Tail exponent failed: %s", exc)
        return {"error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# Baum — Hidden Markov Model regime detection
# ═══════════════════════════════════════════════════════════════

def detect_regime(
    closes: list[float],
    volumes: list[float] | None = None,
    n_regimes: int = 3,
    min_data: int = 100,
) -> dict[str, Any]:
    """
    Baum-Welch (HMM): detect latent market regimes from price data.

    Uses a Gaussian HMM on log-returns (and optionally volume).
    Returns the current regime, its probability, and regime
    characteristics (mean return, volatility per regime).

    Typical regimes discovered:
      0: low-vol / mean-reverting (sideways)
      1: trending up (bull)
      2: trending down (bear) or high-vol
    """
    try:
        from hmmlearn.hmm import GaussianHMM
    except ImportError:
        return {"error": "hmmlearn not installed; cannot run HMM regime detection"}

    if len(closes) < min_data:
        return {"error": f"Need at least {min_data} data points, got {len(closes)}"}

    try:
        prices = np.array(closes, dtype=np.float64)
        log_returns = np.diff(np.log(prices))
        if len(log_returns) < min_data - 1:
            return {"error": "Insufficient returns after log-transform"}

        # Build feature matrix
        features = log_returns.reshape(-1, 1)
        if volumes is not None and len(volumes) == len(closes):
            vol_array = np.array(volumes, dtype=np.float64)
            vol_rel = np.zeros_like(log_returns)
            for i in range(len(log_returns)):
                window = vol_array[max(0, i - 19):i + 1]
                avg_vol = float(np.mean(window)) if len(window) > 0 else 1.0
                vol_rel[i] = vol_array[i + 1] / avg_vol if avg_vol > 0 else 1.0
            features = np.column_stack([log_returns, vol_rel])

        # Fit HMM
        model = GaussianHMM(
            n_components=min(n_regimes, 3),
            covariance_type="full",
            n_iter=200,
            random_state=42,
        )
        model.fit(features)

        # Predict regime sequence
        hidden_states = model.predict(features)
        current_regime = int(hidden_states[-1])
        probs = model.predict_proba(features)
        current_prob = float(probs[-1, current_regime])

        # Per-regime statistics
        regimes = {}
        regime_names = {
            0: "sideways / mean-reverting",
            1: "bull trending",
            2: "bear / high-vol",
        }
        for r in range(model.n_components):
            mask = hidden_states == r
            regime_returns = log_returns[mask]
            if len(regime_returns) > 0:
                regimes[str(r)] = {
                    "label": regime_names.get(r, f"regime_{r}"),
                    "count": int(np.sum(mask)),
                    "mean_daily_return_pct": round(float(np.mean(regime_returns)) * 100, 4),
                    "vol_daily_pct": round(float(np.std(regime_returns, ddof=1)) * 100, 3),
                    "fraction_of_sample": round(float(np.mean(mask)) * 100, 1),
                }

        # Recent regime stability
        recent_10 = hidden_states[-10:]
        stability = float(np.mean(recent_10 == current_regime))

        return {
            "current_regime": current_regime,
            "current_regime_label": regime_names.get(current_regime, f"regime_{current_regime}"),
            "current_probability_pct": round(current_prob * 100, 1),
            "regime_stability_pct": round(stability * 100, 1),
            "total_bars": int(len(log_returns)),
            "regimes": regimes,
            "interpretation": (
                f"Regime atual: {regime_names.get(current_regime, current_regime)} "
                f"({current_prob*100:.0f}% confiança). "
                f"Estabilidade recente (10 barras): {stability*100:.0f}%. "
                f"Dos {len(log_returns)} períodos analisados, "
                f"{regimes[str(current_regime)]['fraction_of_sample']:.0f}% "
                f"estiveram neste regime."
            ),
        }
    except Exception as exc:
        logger.warning("HMM regime detection failed: %s", exc)
        return {"error": f"HMM failed: {exc}"}


# ═══════════════════════════════════════════════════════════════
# Ed Thorp — Kelly Criterion optimal position sizing
# ═══════════════════════════════════════════════════════════════

def kelly_fraction(
    win_rate: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    max_fraction: float = 0.25,
) -> dict[str, Any]:
    """
    Ed Thorp: Kelly Criterion determines the optimal fraction of
    capital to bet for maximum long-term growth.

    f* = (p * b - q) / b
    where p = win_rate, b = avg_win / avg_loss, q = 1-p

    Half-Kelly is recommended for real trading (conservative).
    """
    if not (0 < win_rate < 1):
        return {"error": "win_rate must be between 0 and 1"}
    if avg_win_pct <= 0 or avg_loss_pct <= 0:
        return {"error": "avg_win_pct and avg_loss_pct must be positive"}

    try:
        b = avg_win_pct / avg_loss_pct  # odds ratio
        q = 1.0 - win_rate
        f_star = (win_rate * b - q) / b

        # Clamp
        f_star_clamped = max(0.0, min(f_star, max_fraction))
        half_kelly = f_star_clamped / 2.0

        if f_star <= 0:
            verdict = "NEGATIVO — Kelly sugere não tomar posição"
        elif f_star < 0.05:
            verdict = "CONSERVADOR — posição pequena justificada"
        elif f_star < 0.15:
            verdict = "MODERADO — posição razoável"
        else:
            verdict = "AGRESSIVO — edge forte, mas Half-Kelly recomendado"

        return {
            "win_rate_pct": round(win_rate * 100, 1),
            "avg_win_pct": round(avg_win_pct, 2),
            "avg_loss_pct": round(avg_loss_pct, 2),
            "odds_ratio": round(b, 2),
            "full_kelly_pct": round(f_star * 100, 1),
            "half_kelly_pct": round(half_kelly * 100, 1),
            "verdict": verdict,
            "interpretation": (
                f"Kelly full: {f_star*100:.1f}% do capital. "
                f"Half-Kelly (recomendado): {half_kelly*100:.1f}%. {verdict}"
            ),
        }
    except Exception as exc:
        logger.warning("Kelly failed: %s", exc)
        return {"error": str(exc)}


def kelly_from_history(
    trade_results: list[float],
    max_fraction: float = 0.25,
) -> dict[str, Any]:
    """Compute Kelly fraction from a list of trade P&L values."""
    if len(trade_results) < 5:
        return {"error": "Need at least 5 trades for Kelly estimation"}
    try:
        wins = [r for r in trade_results if r > 0]
        losses = [abs(r) for r in trade_results if r < 0]
        if not wins or not losses:
            return {"error": "Need both winning and losing trades"}
        win_rate = len(wins) / len(trade_results)
        avg_win = float(np.mean(wins))
        avg_loss = float(np.mean(losses))
        return kelly_fraction(win_rate, avg_win, avg_loss, max_fraction)
    except Exception as exc:
        return {"error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# Black-Scholes-Merton — placeholder (needs options data)
# ═══════════════════════════════════════════════════════════════

def implied_metrics(
    spot: float,
    strike: float,
    days_to_expiry: int,
    option_price: float,
    is_call: bool = True,
    risk_free_rate: float = 0.03,
) -> dict[str, Any]:
    """
    Black-Scholes-Merton: compute implied volatility and Greeks
    from an option price.  Uses a simple bisection search for σ.

    This is a placeholder until we have an options data feed.
    """
    from scipy.stats import norm

    try:
        T = days_to_expiry / 365.0
        if T <= 0:
            return {"error": "Option expired or expiry date invalid"}

        # Bisection search for implied volatility
        def bs_price(sigma: float) -> float:
            if sigma <= 0:
                return -1
            d1 = (math.log(spot / strike) + (risk_free_rate + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            if is_call:
                return spot * norm.cdf(d1) - strike * math.exp(-risk_free_rate * T) * norm.cdf(d2)
            else:
                return strike * math.exp(-risk_free_rate * T) * norm.cdf(-d2) - spot * norm.cdf(-d1)

        lo, hi = 0.001, 5.0
        for _ in range(100):
            mid = (lo + hi) / 2
            price_mid = bs_price(mid)
            if price_mid < 0:
                return {"error": "BS price negative — check inputs"}
            if abs(price_mid - option_price) < 0.0001:
                break
            if price_mid < option_price:
                lo = mid
            else:
                hi = mid
        sigma = (lo + hi) / 2

        # Greeks
        d1 = (math.log(spot / strike) + (risk_free_rate + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        delta = norm.cdf(d1) if is_call else norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (spot * sigma * math.sqrt(T))

        return {
            "spot": spot,
            "strike": strike,
            "days_to_expiry": days_to_expiry,
            "option_type": "call" if is_call else "put",
            "implied_vol_pct": round(sigma * 100, 1),
            "delta": round(delta, 3),
            "gamma": round(gamma, 6),
            "probability_itm_pct": round(abs(norm.cdf(d2 if is_call else -d2)) * 100, 1),
            "interpretation": (
                f"Volatilidade implícita: {sigma*100:.1f}%. "
                f"Probabilidade ITM: {abs(norm.cdf(d2 if is_call else -d2))*100:.0f}%. "
                f"Delta: {delta:.3f}."
            ),
        }
    except Exception as exc:
        logger.warning("BS implied metrics failed: %s", exc)
        return {"error": f"Black-Scholes failed: {exc}"}
