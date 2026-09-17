from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from tradingagents.dataflows.math_tools import (
    detect_regime,
    implied_metrics,
    kelly_fraction,
    tail_exponent,
)


def test_regime_labels_follow_economics_not_state_id(monkeypatch):
    import hmmlearn.hmm
    returns = np.tile([-.01, -.012, .02, .023], 30)
    prices = (100 * np.exp(np.r_[0, np.cumsum(returns)])).tolist()
    states = (returns > 0).astype(int)

    class Model:
        def __init__(self, **kwargs):
            self.n_components = 2
            self.tol = .01
            self.monitor_ = SimpleNamespace(converged=True, history=[1., 1.001])

        def fit(self, features):
            assert np.allclose(features.mean(axis=0), 0, atol=1e-8)

        def score(self, features):
            return 1.

        def predict(self, features):
            return states

        def predict_proba(self, features):
            return np.eye(2)[states]

    monkeypatch.setattr(hmmlearn.hmm, "GaussianHMM", Model)
    first = detect_regime(prices, n_regimes=2)
    states = 1 - states
    second = detect_regime(prices, n_regimes=2)
    assert first["current_regime"] != second["current_regime"]
    assert first["current_regime_label"] == second["current_regime_label"] == "retorno positivo (bull)"
    monkeypatch.setattr(Model, "score", lambda *args: float("nan"))
    assert "error" in detect_regime(prices, n_regimes=2)
    monkeypatch.setattr(Model, "score", lambda *args: 1.)
    monkeypatch.setattr(Model, "fit", lambda self, features: setattr(self.monitor_, "converged", False))
    assert "error" in detect_regime(prices, n_regimes=2)
    monkeypatch.setattr(Model, "fit", lambda self, features: setattr(self.monitor_, "history", [1., 2.]))
    assert "error" in detect_regime(prices, n_regimes=2)


def test_invalid_quant_inputs_and_shared_kelly():
    from tradingagents.agents.utils.position_sizing import calculate_kelly_fraction
    assert "error" in tail_exponent([0.] * 100)
    assert "error" in tail_exponent([.01] * 100)
    assert "error" in detect_regime(list(range(1, 120)), [-1] * 119)
    assert "error" in implied_metrics(100, 100, 30, 101)
    assert "error" in kelly_fraction(float("nan"), 1, 1)
    assert calculate_kelly_fraction(.9, 2, 1)["half_kelly"] == .25
    # Known one-year, zero-rate, at-the-money Black-Scholes call at sigma .20.
    assert implied_metrics(100, 100, 365, 7.965567455, risk_free_rate=0)["implied_vol_pct"] == 20.


def test_ava_narrative_does_not_override_rating():
    from tradingagents.agents.utils.rating import extract_rating
    assert extract_rating("Classificação: Hold\n- **Ação**: esperar por confirmação.") == "Hold"
    assert extract_rating("Classificação: Hold\nAção: Buy") is None


@pytest.mark.parametrize("reply", ["Classificação: Sell", "Classificação: Buy\nAlvo 9999,99"])
def test_professor_rejects_changed_rating_or_invented_level(reply):
    from tradingagents.agents.risk_mgmt.professor import create_professor
    from tradingagents.agents.utils.rating import extract_rating
    llm = MagicMock()
    llm.invoke.return_value.content = reply
    result = create_professor(llm)({"final_trade_decision": "Classificação: Buy\nPreço 123,45"})
    assert extract_rating(result["professor_message"]) == "Buy"
    assert "9999" not in result["professor_message"]


def test_historical_collector_routes_dates_and_withholds_live(monkeypatch):
    import tradingagents.graph.trading_graph as module
    calls = []

    def route(name, *args, **kwargs):
        calls.append((name, args, kwargs))
        return "data"

    monkeypatch.setattr(module, "route_to_vendor", route)
    graph = object.__new__(module.TradingAgentsGraph)
    result = graph.collect_data("MSFT", "2020-01-10")
    assert ("get_indicators", ("MSFT", "rsi", "2020-01-10", 30), {}) in calls
    assert not any(call[0] in {"get_prediction_markets", "get_fundamentals", "get_balance_sheet"} for call in calls)
    assert "histórica" in result["market_session"]
    assert "publication vintage" in result["collection_errors"]


def test_session_is_not_a_verified_calendar():
    from datetime import datetime

    from tradingagents.dataflows.market_sessions import get_market_session_info
    result = get_market_session_info("MSFT", dt=datetime(2026, 12, 25, 12))
    assert result["calendar_verified"] is False
    assert "não verificado" in result["agent_guidance"]
    assert get_market_session_info("SAP.DE")["exchange"] == "unknown"


@pytest.mark.parametrize("with_math", [True, False])
def test_math_through_complete_graph_and_reports(tmp_path, monkeypatch, with_math):
    from langchain_core.messages import AIMessage
    from langgraph.prebuilt import ToolNode

    import tradingagents.agents.analysts.math_analyst as math_module
    import tradingagents.agents.trader.trader as trader_module
    from tradingagents.graph.conditional_logic import ConditionalLogic
    from tradingagents.graph.propagation import Propagator
    from tradingagents.graph.setup import GraphSetup
    from tradingagents.reporting import write_report_tree

    close = 100 + np.sin(np.arange(40))
    monkeypatch.setattr(math_module, "load_ohlcv", lambda *a: pd.DataFrame({"Close": close, "Volume": 1000}))
    monkeypatch.setattr(trader_module, "get_atr_position_sizing", SimpleNamespace(invoke=lambda _: "ATR indisponível"))

    class Model:
        prompts = []

        def invoke(self, prompt):
            self.prompts.append(str(prompt))
            return AIMessage(content="Classificação: Hold\n## Análise\nTeste simulado.\n## Validação\nDados simulados.\n## Ação\nManter.")

    model = Model()
    import tradingagents.graph.setup as setup_module
    monkeypatch.setattr(setup_module, "create_market_analyst", lambda _: lambda state: {
        "messages": [AIMessage(content="Mercado simulado")], "market_report": "Mercado simulado",
    })
    selected = ["math"] if with_math else ["market"]
    graph = GraphSetup(model, model, {selected[0]: ToolNode([])}, ConditionalLogic()).setup_graph(selected)
    # setup_graph returns an uncompiled StateGraph for checkpoint support.
    if hasattr(graph, "compile"):
        graph = graph.compile()
    state = Propagator().create_initial_state("MSFT", "2025-01-01")
    result = graph.invoke(state, {"recursion_limit": 100})
    if with_math:
        assert result["quantitative_results"]["bars"] == 40
        assert result["math_report"]
    else:
        assert result["math_report"] == ""
    assert "Classificação" in result["professor_message"]
    if with_math:
        assert sum("Evidência quantitativa" in prompt for prompt in model.prompts) >= 5
    report = write_report_tree(result, "MSFT", tmp_path)
    if with_math:
        assert "Evidência quantitativa" in report.read_text(encoding="utf-8")
    else:
        assert "Mercado simulado" in report.read_text(encoding="utf-8")
