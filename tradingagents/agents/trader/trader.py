"""Trader: turns the Research Manager's investment plan into a concrete transaction proposal."""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = get_instrument_context_from_state(state)
        investment_plan = state["investment_plan"]

        messages = [
            {
                "role": "system",
                "content": (
                    "És um agente de trading a analisar dados de mercado para tomar decisões de investimento. "
                    "Com base na tua análise, fornece uma recomendação específica para comprar, vender ou manter. "
                    "Fundamenta o teu raciocínio nos relatórios dos analistas e no plano de investigação."
                    + get_language_instruction()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Com base numa análise abrangente de uma equipa de analistas, aqui está um plano "
                    f"de investimento adaptado para {company_name}. {instrument_context} Este plano incorpora "
                    f"informações de tendências técnicas atuais do mercado, indicadores macroeconómicos e "
                    f"sentimento das redes sociais. Usa este plano como base para avaliar a tua próxima "
                    f"decisão de trading.\n\nPlano de Investimento Proposto: {investment_plan}\n\n"
                    f"Aproveita estas informações para tomar uma decisão informada e estratégica."
                ),
            },
        ]

        trader_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            messages,
            render_trader_proposal,
            "Trader",
        )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
