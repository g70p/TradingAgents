"""Research Manager: turns the bull/bear debate into an investment plan for the trader."""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.volume_framework import VOLUME_FRAMEWORK



def create_research_manager(llm):

    def research_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        history = state["investment_debate_state"].get("history", "")

        investment_debate_state = state["investment_debate_state"]

        prompt = f"""Enquanto Gestor de Investigação e facilitador do debate, a tua função é avaliar criticamente esta ronda do debate e apresentar um plano de investimento claro e acionável para o trader.

**⚠️ FORMATO OBRIGATÓRIO — AVA ⚠️**
Toda a tua resposta DEVE seguir o método AVA (Análise → Validação → Ação).

{instrument_context}

---

**Escala de Classificação** (usa exatamente uma):
- **Comprar**: Forte convicção na tese bull; recomenda assumir ou aumentar a posição
- **Sobreponderar**: Visão construtiva; recomenda aumentar gradualmente a exposição
- **Manter**: Visão equilibrada; recomenda manter a posição atual
- **Subponderar**: Visão cautelosa; recomenda reduzir a exposição
- **Vender**: Forte convicção na tese bear; recomenda sair ou evitar a posição

Assume uma posição clara sempre que os argumentos mais fortes do debate o justifiquem; reserva Manter para situações em que as evidências de ambos os lados estão genuinamente equilibradas.

---

**Histórico do Debate:**
{history}

---

## AVA — Análise, Validação, Ação
- **Análise**: <pesa os argumentos bull vs bear, identifica o lado com maior peso de evidências>
- **Validação**: <confirmação cruzada com os dados de mercado; há divergências?>
- **Ação**: <plano de investimento claro e acionável: rating + justificação>""" + VOLUME_FRAMEWORK + get_language_instruction()

        response = llm.invoke(prompt)
        investment_plan = str(response.content) if hasattr(response, 'content') else str(response)

        new_investment_debate_state = {
            "judge_decision": investment_plan,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": investment_plan,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": investment_plan,
        }

    return research_manager_node
