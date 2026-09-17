"""Report parity: the shared writer produces the report tree for the CLI and the
programmatic API alike (#1037)."""

from types import SimpleNamespace

import pytest

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.reporting import write_report_tree


def _state():
    return {
        "market_report": "MKT",
        "news_report": "NEWS",
        "investment_debate_state": {"judge_decision": "RM PLAN"},
        "trader_investment_plan": "TRADE",
        "risk_debate_state": {"judge_decision": "PM DECISION"},
    }


@pytest.mark.unit
def test_write_report_tree_creates_files(tmp_path):
    out = write_report_tree(_state(), "AAPL", tmp_path)
    assert out.name == "relatorio_completo.md"
    assert (tmp_path / "mercado.md").read_text(encoding="utf-8") == "MKT"
    assert (tmp_path / "noticias.md").read_text(encoding="utf-8") == "NEWS"
    assert (tmp_path / "gestor_investigacao.md").read_text(encoding="utf-8") == "RM PLAN"
    assert (tmp_path / "trader.md").read_text(encoding="utf-8") == "TRADE"
    assert (tmp_path / "decisao_portfolio.md").read_text(encoding="utf-8") == "PM DECISION"
    complete = out.read_text(encoding="utf-8")
    assert "Relatório TradingAgents — AAPL" in complete
    assert "MKT" in complete and "PM DECISION" in complete


@pytest.mark.unit
def test_save_reports_explicit_path(tmp_path):
    # Unbound: with an explicit save_path, the method doesn't touch self/config.
    out = TradingAgentsGraph.save_reports(None, _state(), "AAPL", save_path=tmp_path)
    assert (tmp_path / "relatorio_completo.md").exists()
    assert out == tmp_path / "relatorio_completo.md"


@pytest.mark.unit
def test_save_reports_defaults_under_results_dir(tmp_path):
    mock_self = SimpleNamespace(config={"results_dir": str(tmp_path)})
    out = TradingAgentsGraph.save_reports(mock_self, _state(), "AAPL")
    assert out.exists()
    assert out.parent.parent.name == "reports"  # results_dir/reports/AAPL_<stamp>/...
    assert out.parent.name.startswith("AAPL_")
