"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path``. The
CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless / API
run produces the same on-disk report tree a CLI run does.
"""

from datetime import datetime
from pathlib import Path


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analistas"
    analyst_parts = []
    if final_state.get("market_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "mercado.md").write_text(final_state["market_report"], encoding="utf-8")
        analyst_parts.append(("Analista de Mercado", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentimento.md").write_text(final_state["sentiment_report"], encoding="utf-8")
        analyst_parts.append(("Analista de Sentimento", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "noticias.md").write_text(final_state["news_report"], encoding="utf-8")
        analyst_parts.append(("Analista de Notícias", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentais.md").write_text(final_state["fundamentals_report"], encoding="utf-8")
        analyst_parts.append(("Analista de Fundamentais", final_state["fundamentals_report"]))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Relatórios da Equipa de Analistas\n\n{content}")

    # 2. Research
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_investigacao"
        debate = final_state["investment_debate_state"]
        research_parts = []
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "touro.md").write_text(debate["bull_history"], encoding="utf-8")
            research_parts.append(("Investigador Touro", debate["bull_history"]))
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "urso.md").write_text(debate["bear_history"], encoding="utf-8")
            research_parts.append(("Investigador Urso", debate["bear_history"]))
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "gestor.md").write_text(debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Gestor de Investigação", debate["judge_decision"]))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Decisão da Equipa de Investigação\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"], encoding="utf-8")
        sections.append(f"## III. Plano da Equipa de Trading\n\n### Trader\n{final_state['trader_investment_plan']}")

    # 4. Risk Management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risco"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "agressivo.md").write_text(risk["aggressive_history"], encoding="utf-8")
            risk_parts.append(("Analista Agressivo", risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservador.md").write_text(risk["conservative_history"], encoding="utf-8")
            risk_parts.append(("Analista Conservador", risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutro.md").write_text(risk["neutral_history"], encoding="utf-8")
            risk_parts.append(("Analista Neutro", risk["neutral_history"]))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Decisão da Equipa de Gestão de Risco\n\n{content}")

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decisao.md").write_text(risk["judge_decision"], encoding="utf-8")
            sections.append(f"## V. Decisão do Gestor de Portfólio\n\n### Gestor de Portfólio\n{risk['judge_decision']}")

    # Write consolidated report
    header = f"# Relatório de Análise de Trading: {ticker}\n\nGerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    (save_path / "relatorio_completo.md").write_text(header + "\n\n".join(sections), encoding="utf-8")
    return save_path / "relatorio_completo.md"
