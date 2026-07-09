"""Trader: turns the Research Manager's investment plan into a concrete transaction proposal.

Now includes ATR-based position sizing via a tool that the LLM can invoke
for volatility-adjusted stop-loss and position size recommendations.
"""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.atr_sizing_tool import get_atr_position_sizing
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")
    llm_with_tools = llm.bind_tools([TraderProposal])

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        trade_date = state["trade_date"]

        # Fetch ATR sizing upfront — avoids structured-output tool conflict
        atr_sizing_text = ""
        try:
            atr_sizing_text = get_atr_position_sizing.invoke({
                "ticker": company_name,
                "trade_date": trade_date,
                "account_balance": 100000.0,
            })
        except Exception:
            atr_sizing_text = "ATR não disponível para dimensionamento."

        company_name = state["company_of_interest"]
        trade_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)
        investment_plan = state["investment_plan"]
        current_date = state["trade_date"]
        asset_type = state.get("asset_type", "stock")

        messages = [
            {
                "role": "system",
                "content": (
                    "És um agente de trading a analisar dados de mercado para tomar decisões de investimento. "
                    "Com base na tua análise, fornece uma recomendação específica para comprar, vender ou manter. "
                    "Fundamenta o teu raciocínio nos relatórios dos analistas e no plano de investigação. "
                    "Usa os dados de dimensionamento ATR fornecidos abaixo para definir stop-loss e tamanho de posição."
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
                    f"decisão de trading.\\n\\nPlano de Investimento Proposto: {investment_plan}\\n\\n"
                    f"### Dimensionamento ATR (pré-calculado)\\n{atr_sizing_text}\\n\\n"
                    f"Produz a tua recomendação final de trading para {company_name}."
                ),
            },
        ]

        # Single LLM call — ATR data already injected in the prompt
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
