"""Quantitative analyst: fetch dated prices, calculate, then explain the evidence.

Price arrays never come from LLM-generated prose. Tool results are retained in
state and rendered verbatim alongside the interpretation for traceability.
"""
from __future__ import annotations

import json
import logging

import numpy as np
from langchain_core.messages import AIMessage

from tradingagents.agents.utils.agent_utils import get_language_instruction
from tradingagents.dataflows.math_tools import detect_regime, expected_price_range, tail_exponent
from tradingagents.dataflows.stockstats_utils import load_ohlcv

logger = logging.getLogger(__name__)


def create_math_analyst(llm):
    def math_node(state):
        ticker, date = state["company_of_interest"], state["trade_date"]
        try:
            frame = load_ohlcv(ticker, date)
            closes = frame["Close"].tolist()
            volumes = frame["Volume"].tolist() if "Volume" in frame else None
            if not closes or any(not np.isfinite(p) or p <= 0 for p in closes):
                raise ValueError("Preços inválidos ou ausentes")
            returns = np.diff(np.log(closes)).tolist()
            results = {
                "ticker": ticker, "as_of": date, "source": "Yahoo Finance OHLCV",
                "bars": len(closes),
                "range": expected_price_range(closes, annualization_days=365 if state.get("asset_type") == "crypto" else 252),
                "tail": tail_exponent(returns),
                "regime": detect_regime(closes, volumes),
                "kelly": {"error": "Indisponível sem histórico validado de operações comparáveis"},
                "options": {"error": "Indisponível sem cotações de opções verificadas"},
            }
        except Exception as exc:
            logger.warning("Quantitative data unavailable for %s: %s", ticker, exc)
            results = {"ticker": ticker, "as_of": date, "error": str(exc)}
        evidence = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False)
        report = "## Evidência quantitativa calculada\n```json\n" + evidence + "\n```"
        if "error" not in results:
            prompt = (
                "És o analista quantitativo. Explica os resultados fornecidos em formato AVA. "
                "Não inventes números nem chames ferramentas. Não há garantia de previsão; "
                "resultados indisponíveis devem manter-se indisponíveis. As regras de volume "
                "são hipóteses que precisam de evidência, não conclusões automáticas. "
                + get_language_instruction() + "\n" + evidence
            )
            response = llm.invoke(prompt)
            report += "\n\n## Interpretação\n" + str(response.content)
        else:
            report += "\n\nAnálise quantitativa indisponível; rever os dados antes de concluir."
        return {"messages": [AIMessage(content=report)], "math_report": report,
                "quantitative_results": results}
    return math_node
