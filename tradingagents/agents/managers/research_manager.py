"""Research Manager: turns the bull/bear debate into a structured investment plan for the trader."""

from __future__ import annotations

from tradingagents.agents.schemas import ResearchPlan, render_research_plan
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_research_manager(llm):
    structured_llm = bind_structured(llm, ResearchPlan, "Research Manager")

    def research_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        history = state["investment_debate_state"].get("history", "")

        investment_debate_state = state["investment_debate_state"]

        prompt = f"""Enquanto Gestor de Investigação e facilitador do debate, a tua função é avaliar criticamente esta ronda do debate e apresentar um plano de investimento claro e acionável para o trader.

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
{history}""" + get_language_instruction()

        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_research_plan,
            "Research Manager",
        )

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
