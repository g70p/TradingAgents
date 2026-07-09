"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path`` using
the standardised PT-PT report template.
"""

from datetime import datetime
from pathlib import Path


def _section(title: str, content: str | None) -> str:
    """Format a report section with title, or empty string if no content."""
    if not content or not content.strip():
        return ""
    return f"## {title}\n\n{content.strip()}"


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    asset_type = final_state.get("asset_type", "stock")

    # Extract state fields with safe fallbacks
    market = final_state.get("market_report", "")
    sentiment = final_state.get("sentiment_report", "")
    news = final_state.get("news_report", "")
    fundamentals = final_state.get("fundamentals_report", "")
    trader_plan = final_state.get("trader_investment_plan", "")

    debate = final_state.get("investment_debate_state", {}) or {}
    bull = debate.get("bull_history", "")
    bear = debate.get("bear_history", "")
    research_decision = debate.get("judge_decision", "")

    risk = final_state.get("risk_debate_state", {}) or {}
    aggressive = risk.get("aggressive_history", "")
    conservative = risk.get("conservative_history", "")
    neutral = risk.get("neutral_history", "")
    portfolio_decision = risk.get("judge_decision", "")
    final_trade = final_state.get("final_trade_decision", portfolio_decision)

    # Write individual files
    if market:
        (save_path / "mercado.md").write_text(market, encoding="utf-8")
    if sentiment:
        (save_path / "sentimento.md").write_text(sentiment, encoding="utf-8")
    if news:
        (save_path / "noticias.md").write_text(news, encoding="utf-8")
    if fundamentals:
        (save_path / "fundamentais.md").write_text(fundamentals, encoding="utf-8")
    if bull:
        (save_path / "touro.md").write_text(bull, encoding="utf-8")
    if bear:
        (save_path / "urso.md").write_text(bear, encoding="utf-8")
    if research_decision:
        (save_path / "gestor_investigacao.md").write_text(research_decision, encoding="utf-8")
    if trader_plan:
        (save_path / "trader.md").write_text(trader_plan, encoding="utf-8")
    if aggressive:
        (save_path / "risco_agressivo.md").write_text(aggressive, encoding="utf-8")
    if conservative:
        (save_path / "risco_conservador.md").write_text(conservative, encoding="utf-8")
    if neutral:
        (save_path / "risco_neutro.md").write_text(neutral, encoding="utf-8")
    if portfolio_decision:
        (save_path / "decisao_portfolio.md").write_text(portfolio_decision, encoding="utf-8")

    # ── Consolidated report with standardised template ──────────────────

    # Extract ticker metadata from state
    company_name = final_state.get("company_of_interest", ticker)
    exchange = final_state.get("exchange", final_state.get("instrument_context", ""))
    if hasattr(exchange, "exchange"):
        exchange = exchange.exchange or ""
    exchange = str(exchange)[:80] if exchange else "N/D"

    market_context = final_state.get("market_session_context", "N/D")

    # Build consolidated report
    parts = []
    parts.append(f"# Relatório TradingAgents — {ticker} | {final_state.get('trade_date', 'N/D')}")
    parts.append("")

    # 0. Overview
    parts.append("## 0. Visão Geral")
    parts.append("")
    parts.append(f"| Campo | Valor |")
    parts.append(f"|---|---|")
    parts.append(f"| **Ticker** | {ticker} |")
    parts.append(f"| **Empresa/Ativo** | {company_name} |")
    parts.append(f"| **Bolsa** | {exchange} |")
    parts.append(f"| **Data da Análise** | {final_state.get('trade_date', 'N/D')} |")
    parts.append(f"| **Tipo de Ativo** | {asset_type} |")
    parts.append(f"| **Estado do Mercado** | {str(market_context)[:120]} |")
    parts.append("")

    # 1. Analysts
    if market:
        parts.append(_section("1. Análise Técnica", market))
    if sentiment:
        parts.append(_section("2. Análise de Sentimento", sentiment))
    if news:
        parts.append(_section("3. Análise de Notícias e Macro", news))
    if fundamentals:
        parts.append(_section("4. Análise Fundamental", fundamentals))

    # 2. Research Debate
    if bull or bear or research_decision:
        parts.append("## 5. Investigação (Debate Bull vs Bear)")
        parts.append("")
        if bull:
            parts.append(f"### Análise do Touro\n\n{bull.strip()}")
            parts.append("")
        if bear:
            parts.append(f"### Análise do Urso\n\n{bear.strip()}")
            parts.append("")
        if research_decision:
            parts.append(f"### Decisão do Gestor de Investigação\n\n{research_decision.strip()}")
            parts.append("")

    # 3. Trading Plan
    if trader_plan:
        parts.append(_section("6. Plano de Trading", trader_plan))

    # 4. Risk Management
    if aggressive or conservative or neutral:
        parts.append("## 7. Gestão de Risco")
        parts.append("")
        if aggressive:
            parts.append(f"### Análise Agressiva\n\n{aggressive.strip()}")
            parts.append("")
        if conservative:
            parts.append(f"### Análise Conservadora\n\n{conservative.strip()}")
            parts.append("")
        if neutral:
            parts.append(f"### Análise Neutra\n\n{neutral.strip()}")
            parts.append("")

    # 5. Portfolio Decision
    if portfolio_decision:
        parts.append(_section("8. Decisão Final do Gestor de Portfólio", portfolio_decision))

    # 6. Final trade signal
    if final_trade:
        parts.append("## 9. Sinal Final de Trading")
        parts.append("")
        parts.append(f"**{final_trade}**")
        parts.append("")

    # Footer
    parts.append("---")
    parts.append("")
    parts.append(f"**Framework:** TradingAgents PT-PT (fork G70P)  |  **Gerado:** {now.strftime('%Y-%m-%d %H:%M:%S')}  |  **Fonte:** [github.com/G70P/TradingAgents](https://github.com/G70P/TradingAgents)")
    parts.append("")

    report_content = "\n".join(parts)
    report_file = save_path / "relatorio_completo.md"
    report_file.write_text(report_content, encoding="utf-8")

    return report_file
