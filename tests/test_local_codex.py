"""The supported local route must work without any model provider installed."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from tradingagents import local
from tradingagents.dataflows.math_tools import expected_price_range, kelly_fraction


def prices():
    close = 100 * np.exp(np.cumsum(np.sin(np.arange(40)) * .01))
    return pd.DataFrame({"Date": pd.date_range("2025-01-01", periods=40), "Open": close,
                         "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1000})


def test_dossier_offline_dates_hashes_and_no_llm(tmp_path, monkeypatch):
    import builtins
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.startswith(("langchain", "langgraph", "openai", "anthropic", "tradingagents.llm_clients")):
            raise AssertionError(f"Local route imported model infrastructure: {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(local, "load_ohlcv", lambda *a: pytest.fail("CSV must not fetch prices"))
    monkeypatch.setattr(local, "fetch_google_news_for_ticker", lambda *a, **k: pytest.fail("News disabled"))
    csv = tmp_path / "input.csv"
    prices().to_csv(csv, index=False)
    run = local.prepare_dossier("MSFT", "2025-02-05", tmp_path, csv=csv, news=False)
    manifest = json.loads((run / "manifesto.json").read_text())
    assert manifest["latest_bar"] == "2025-02-05"
    assert manifest["bars"] == 36
    assert manifest["analysis_status"] == "pending_codex"
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((run / name).read_bytes()).hexdigest() == digest
    assert not (run / "relatorio.md").exists()


def test_online_sources_are_dated(tmp_path, monkeypatch):
    monkeypatch.setattr(local, "load_ohlcv", lambda ticker, date: prices())
    calls = []

    def news(ticker, **kwargs):
        calls.append((ticker, kwargs))
        return ""

    monkeypatch.setattr(local, "fetch_google_news_for_ticker", news)
    run = local.prepare_dossier("MSFT", "2025-02-05", tmp_path)
    manifest = json.loads((run / "manifesto.json").read_text())
    assert calls == [("MSFT", {"start_date": "2025-01-29", "end_date": "2025-02-05"})]
    assert manifest["errors"]


@pytest.mark.parametrize("column,value", [("Close", float("nan")), ("Volume", -1), ("High", 1), ("Date", "bad")])
def test_invalid_input_is_rejected(column, value):
    frame = prices().astype({column: object})
    frame.loc[0, column] = value
    with pytest.raises((ValueError, TypeError)):
        local.validate_prices(frame, "2025-02-09")


def test_quantile_is_deterministic_and_matches_normal():
    values = prices()["Close"].tolist()
    result = expected_price_range(values, confidence=.95)
    assert result == expected_price_range(values, confidence=.95)
    assert result["z_score"] == pytest.approx(1.959963984540054)


def test_half_kelly_before_cap():
    assert kelly_fraction(.9, 2, 1, max_fraction=.25)["half_kelly_pct"] == 25
