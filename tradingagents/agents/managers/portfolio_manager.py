"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm):
    structured_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lições de decisões e resultados anteriores:\n{past_context}\n"
            if past_context
            else ""
        )

        prompt = f"""Enquanto Gestor de Portfólio, sintetiza o debate dos analistas de risco e emite a decisão final de trading.

{instrument_context}

---

**Escala de Classificação** (usa exatamente uma):
- **Comprar**: Forte convicção para entrar ou aumentar a posição
- **Sobreponderar**: Perspetiva favorável, aumentar gradualmente a exposição
- **Manter**: Manter a posição atual, sem ação necessária
- **Subponderar**: Reduzir a exposição, realizar lucros parciais
- **Vender**: Sair da posição ou evitar a entrada

**Contexto:**
- Plano de investimento do Gestor de Investigação: **{research_plan}**
- Proposta de transação do Trader: **{trader_plan}**
{lessons_line}
**Histórico do Debate dos Analistas de Risco:**
{history}

---

**Formato de Resposta Obrigatório:**

## Decisão Final
**Rating**: <Comprar|Sobreponderar|Manter|Subponderar|Vender>
**Ação**: <Buy|Overweight|Hold|Underweight|Sell>
**Preço de Entrada**: <float>
**Stop Loss**: <float>
**Dimensionamento de Posição**: <percentagem ou descrição>

## Raciocínio
<parágrafo conciso>

## AVA — Análise, Validação, Ação
- **Análise**: <síntese dos factos-chave do debate>
- **Validação**: <confirmação cruzada entre analistas e dados>
- **Ação**: <decisão final justificada>

Sê decisivo e fundamenta cada conclusão em evidências específicas dos analistas.{get_language_instruction()}"""

        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_pm_decision,
            "Portfolio Manager",
        )

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
        }

    return portfolio_manager_node
