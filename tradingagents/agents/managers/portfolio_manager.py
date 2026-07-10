"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses plain LLM invocation — the prompt includes the expected output format
inline, and the result is stored directly in ``final_trade_decision``.
No structured-output wrapper, no fallback, no unnecessary warnings.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_portfolio_manager(llm):

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

**⚠️ FORMATO OBRIGATÓRIO — AVA ⚠️**
Toda a tua resposta DEVE seguir o método AVA (Análise → Validação → Ação).
NÃO escrevas texto livre fora desta estrutura. Começa SEMPRE com "## Decisão Final".

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

        response = llm.invoke(prompt)
        final_trade_decision = str(response.content) if hasattr(response, 'content') else str(response)

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
