from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage

from tradingagents.agents.risk_mgmt.professor import create_professor
from tradingagents.agents.trader import trader
from tradingagents.agents.utils import atr_sizing_tool
from tradingagents.agents.utils.position_sizing import calculate_atr, calculate_atr_position_size
from tradingagents.agents.utils.rating import extract_rating
from tradingagents.graph.signal_processing import SignalProcessor


def test_atr_units_exposure_and_risk_are_distinct():
    result = calculate_atr_position_size(
        account_balance=10000, current_price=100, atr_value=2,
    )
    assert result["units"] == 25
    assert result["position_size"] == 2500
    assert result["risk_amount"] == 100
    assert result["stop_loss_price"] == 96


def test_exposure_cap_reduces_actual_risk():
    result = calculate_atr_position_size(
        account_balance=10000, current_price=100, atr_value=0.5,
    )
    assert result["units"] == 25
    assert result["risk_amount"] == 25 < result["risk_budget"]


def test_fractional_units_and_short_stop():
    result = calculate_atr_position_size(
        account_balance=10000, current_price=50000, atr_value=1000,
        unit_step=0.001, side="short",
    )
    assert result["units"] == 0.05
    assert result["stop_loss_price"] == 52000


@pytest.mark.parametrize("override", [
    {"atr_value": float("nan")}, {"account_balance": -1}, {"risk_percent": 101},
    {"unit_step": 0}, {"side": "invalid"}, {"atr_value": 100},
])
def test_invalid_sizing_is_explicit(override):
    inputs = {"account_balance": 10000, "current_price": 100, "atr_value": 2}
    with pytest.raises(ValueError):
        calculate_atr_position_size(**(inputs | override))


def test_mismatched_ohlcv_does_not_index_past_end():
    assert calculate_atr([2] * 20, [1], [1.5] * 20) is None


def test_tool_accepts_timezone_aware_bars_and_trims_future(monkeypatch):
    frame = pd.DataFrame({"High": [102] * 21, "Low": [98] * 21, "Close": [100] * 21},
                         index=pd.date_range("2025-05-01", periods=21, tz="Europe/Lisbon"))
    frame.iloc[-1] = [99999, 1, 90000]
    stock = MagicMock()
    stock.history.return_value = frame
    monkeypatch.setattr(atr_sizing_tool.yf, "Ticker", lambda *_: stock)
    result = atr_sizing_tool.get_atr_position_sizing.invoke({
        "ticker": "TEST.LS", "current_date": "2025-05-20",
    })
    assert "Preço Atual**: 100.0000" in result
    assert "Erro" not in result


def test_trader_calls_atr_with_valid_schema_and_includes_technical_report(monkeypatch):
    from tradingagents.dataflows.config import set_config
    set_config({"account_balance": 12345.0, "risk_percent": 0.5})
    calls = []
    monkeypatch.setattr(trader, "get_atr_position_sizing",
                        SimpleNamespace(invoke=lambda args: calls.append(args) or "ATR VERIFIED"))
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="**Rating**: Manter")
    result = trader.create_trader(llm)({
        "company_of_interest": "TEST.LS", "trade_date": "2025-05-20",
        "investment_plan": "PLAN", "market_report": "TECHNICAL EVIDENCE",
    })
    assert calls == [{"ticker": "TEST.LS", "current_date": "2025-05-20",
                      "account_balance": 12345.0, "risk_percent": 0.5}]
    prompt = str(llm.invoke.call_args)
    assert "ATR VERIFIED" in prompt and "TECHNICAL EVIDENCE" in prompt
    assert result["trader_investment_plan"] == "**Rating**: Manter"


@pytest.mark.parametrize("text, expected", [
    ("**Rating**: Comprar\n**Ação**: Buy", "Buy"),
    ("**Rating**: Sobreponderar", "Overweight"),
    ("**Rating**: Manter", "Hold"),
    ("**Rating**: Subponderar", "Underweight"),
    ("**Rating**: Vender", "Sell"),
    ("Rating: Buy\nAção: Sell", None),
    ("Rating: Buy/Sell", None),
    ("O analista quer comprar, mas faltam dados.", None),
    ("Rating: desconhecido\nAção: Buy", None),
])
def test_pt_decisions_and_ambiguity(text, expected):
    assert extract_rating(text) == expected
    assert SignalProcessor().process_signal(text) == (expected or "REVIEW")


def test_professor_does_not_turn_invalid_decision_into_advice():
    llm = MagicMock()
    result = create_professor(llm)({"final_trade_decision": "Dados insuficientes"})
    assert "REVIEW" in result["professor_message"]
    llm.invoke.assert_not_called()
