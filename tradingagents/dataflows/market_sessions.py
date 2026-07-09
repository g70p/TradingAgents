"""Fiscal de Horários e Sessões — Market Session Awareness for TradingAgents.

Injects market status context into every agent so they know whether the market
is open, closed, in pre-market, or after-hours. This directly impacts urgency,
slippage assumptions, and trade recommendation timing.

Supports:
  - Euronext Lisbon (CET/CEST, 08:00–16:30, Mon–Fri)
  - NYSE/NASDAQ (EST/EDT, 09:30–16:00, Mon–Fri)
  - Crypto (24/7, but notes weekend liquidity gaps)
  - Pre-market (30 min before open) and after-hours (post-close)
  - DST-aware timezone handling via zoneinfo
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo


class MarketSession(str, Enum):
    """Market session state for the current instrument."""
    OPEN = "open"                # Regular trading hours
    PRE_MARKET = "pre_market"    # 30 min before open
    AFTER_HOURS = "after_hours"  # After close
    CLOSED = "closed"            # Market closed (weekend, holiday, outside hours)
    ALWAYS_OPEN = "always_open"  # Crypto — 24/7


class MarketExchange(str, Enum):
    """Supported exchange sessions."""
    EURONEXT_LISBON = "euronext_lisbon"
    NYSE = "nyse"
    CRYPTO = "crypto"


# ── Exchange configurations ───────────────────────────────────────────────────

_EXCHANGE_CONFIGS = {
    MarketExchange.EURONEXT_LISBON: {
        "timezone": "Europe/Lisbon",
        "open": time(8, 0),     # 08:00 CET/CEST
        "close": time(16, 30),  # 16:30 CET/CEST
        "pre_market_minutes": 30,
        "label": "Euronext Lisbon",
    },
    MarketExchange.NYSE: {
        "timezone": "America/New_York",
        "open": time(9, 30),    # 09:30 EST/EDT
        "close": time(16, 0),   # 16:00 EST/EDT
        "pre_market_minutes": 30,
        "label": "NYSE/NASDAQ",
    },
}


def _get_exchange_for_ticker(ticker: str, asset_type: str = "stock") -> MarketExchange | None:
    """Determine which exchange a ticker belongs to."""
    if asset_type == "crypto":
        return MarketExchange.CRYPTO

    ticker_upper = ticker.upper()
    # Euronext Lisbon suffixes
    if ticker_upper.endswith(".LS"):
        return MarketExchange.EURONEXT_LISBON
    # Default: NYSE/NASDAQ for US stocks
    return MarketExchange.NYSE


def _get_session_for_exchange(exchange: MarketExchange, dt: datetime | None = None) -> dict:
    """Determine market session for an exchange at a given datetime.

    Returns dict with session, exchange label, local time, next event, and
    a human-readable status string.
    """
    if exchange == MarketExchange.CRYPTO:
        now = dt or datetime.now()
        is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
        return {
            "session": MarketSession.ALWAYS_OPEN,
            "exchange_label": "Cripto (24/7)",
            "local_time": now.strftime("%Y-%m-%d %H:%M UTC"),
            "status": "🟢 Mercado sempre aberto" + (" (fim de semana — liquidez reduzida)" if is_weekend else ""),
            "next_event": "Nenhum — negociação contínua",
            "is_weekend": is_weekend,
        }

    cfg = _EXCHANGE_CONFIGS[exchange]
    tz = ZoneInfo(cfg["timezone"])
    now = dt.astimezone(tz) if dt and dt.tzinfo else (dt or datetime.now(tz))

    if dt and not dt.tzinfo:
        now = dt.replace(tzinfo=tz)

    current_time = now.time()
    weekday = now.weekday()
    is_weekend = weekday >= 5

    open_time = cfg["open"]
    close_time = cfg["close"]
    pre_start = (datetime.combine(now.date(), open_time) - timedelta(minutes=cfg["pre_market_minutes"])).time()

    if is_weekend:
        session = MarketSession.CLOSED
        status = "🔴 Mercado fechado (fim de semana)"
        # Next event: próxima segunda-feira open
        days_to_monday = 7 - weekday if weekday >= 5 else 0
        next_open = (now + timedelta(days=days_to_monday)).replace(
            hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0
        )
        next_event = f"Abre {next_open.strftime('%A %d/%m')} às {open_time.strftime('%H:%M')}"
    elif current_time < pre_start:
        session = MarketSession.CLOSED
        status = "🔴 Mercado fechado"
        next_open = now.replace(hour=open_time.hour, minute=open_time.minute, second=0)
        next_event = f"Abre hoje às {open_time.strftime('%H:%M')}"
    elif current_time < open_time:
        session = MarketSession.PRE_MARKET
        mins_to_open = (datetime.combine(now.date(), open_time) - datetime.combine(now.date(), current_time)).seconds // 60
        status = f"🟡 Pré-mercado (abre em {mins_to_open} min)"
        next_open = now.replace(hour=open_time.hour, minute=open_time.minute, second=0)
        next_event = f"Abre às {open_time.strftime('%H:%M')}"
    elif current_time < close_time:
        session = MarketSession.OPEN
        mins_to_close = (datetime.combine(now.date(), close_time) - datetime.combine(now.date(), current_time)).seconds // 60
        status = f"🟢 Mercado aberto (fecha em {mins_to_close} min)"
        next_close = now.replace(hour=close_time.hour, minute=close_time.minute, second=0)
        next_event = f"Fecha às {close_time.strftime('%H:%M')}"
    else:
        session = MarketSession.AFTER_HOURS
        status = "🟠 Pós-fecho (after-hours)"
        # Next event: tomorrow open
        next_day = now + timedelta(days=1)
        if next_day.weekday() >= 5:
            days_to_monday = 7 - next_day.weekday()
            next_day = now + timedelta(days=days_to_monday)
        next_open = next_day.replace(hour=open_time.hour, minute=open_time.minute, second=0)
        next_event = f"Abre {next_open.strftime('%A %d/%m')} às {open_time.strftime('%H:%M')}"

    return {
        "session": session,
        "exchange_label": cfg["label"],
        "local_time": now.strftime("%Y-%m-%d %H:%M %Z"),
        "status": status,
        "next_event": next_event,
        "timezone": cfg["timezone"],
        "is_weekend": is_weekend,
    }


def get_market_session_info(ticker: str, asset_type: str = "stock", dt: datetime | None = None) -> dict:
    """Get full market session context for a ticker.

    Args:
        ticker: Ticker symbol (e.g. 'BCP.LS', 'NVDA', 'BTC-USD')
        asset_type: 'stock' or 'crypto'
        dt: Datetime to check (defaults to now)

    Returns:
        Dict with session, status, recommendations, and agent guidance
    """
    exchange = _get_exchange_for_ticker(ticker, asset_type)
    info = _get_session_for_exchange(exchange, dt)

    # Add trading implications
    session = info["session"]
    if session == MarketSession.ALWAYS_OPEN:
        info["trading_note"] = "Mercado 24/7 — sem restrições de horário. Atenção à liquidez ao fim de semana."
        info["agent_guidance"] = (
            "O mercado cripto está sempre aberto. As tuas recomendações podem ser executadas "
            "a qualquer momento. Considera que a liquidez é menor aos fins de semana e feriados."
        )
    elif session == MarketSession.OPEN:
        info["trading_note"] = "Mercado aberto — ordens executadas em tempo real."
        info["agent_guidance"] = (
            "O mercado está aberto neste momento. As tuas recomendações de trading podem ser "
            "executadas imediatamente. Usa preços de mercado reais e considera o spread atual."
        )
    elif session == MarketSession.PRE_MARKET:
        info["trading_note"] = "Pré-mercado — ordens podem ser colocadas mas execução limitada."
        info["agent_guidance"] = (
            "Estamos em pré-mercado. As tuas recomendações devem ser para execução na abertura. "
            "Usa preços de fecho anteriores como referência e considera o sentimento overnight."
        )
    elif session == MarketSession.AFTER_HOURS:
        info["trading_note"] = "Pós-fecho — mercado fechado, ordens para o próximo dia."
        info["agent_guidance"] = (
            "O mercado já fechou. As tuas recomendações são para o próximo dia de negociação. "
            "Analisa o fecho de hoje e projeta para amanhã. O after-hours pode ter movimentos "
            "que antecipam a abertura seguinte."
        )
    elif session == MarketSession.CLOSED:
        info["trading_note"] = "Mercado fechado — ordens para o próximo dia útil."
        info["agent_guidance"] = (
            "O mercado está fechado. As tuas recomendações são para o próximo dia de negociação. "
            "Foca-te na análise fundamental e técnica de longo prazo. "
            "Usa o último preço de fecho como referência."
        )

    info["exchange"] = exchange.value if exchange else "unknown"
    return info


def format_market_session_for_prompt(ticker: str, asset_type: str = "stock", dt: datetime | None = None) -> str:
    """Generate a concise market session context block for agent prompts.

    Returns markdown-formatted string ready for injection into any agent's prompt.
    """
    info = get_market_session_info(ticker, asset_type, dt=dt)

    lines = [
        f"## 🕐 Fiscal de Sessão: {info['exchange_label']}",
        f"**Estado**: {info['status']}",
        f"**Hora local**: {info['local_time']}",
        f"**Próximo evento**: {info['next_event']}",
    ]

    if info.get("agent_guidance"):
        lines.append(f"\n**📋 Orientação para os agentes:** {info['agent_guidance']}")

    return "\n".join(lines)


def get_market_context_for_state(ticker: str, asset_type: str = "stock") -> str:
    """Return market session context for injection into the initial graph state.

    Called once at the start of each run so all 11 agents share the same
    market session awareness without each having to recompute it.
    """
    return format_market_session_for_prompt(ticker, asset_type)
