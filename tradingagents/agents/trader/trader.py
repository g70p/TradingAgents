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
    # Bind ATR sizing tool — the LLM can call it for volatility-adjusted sizing
    llm_with_tools = llm.bind_tools([get_atr_position_sizing])

    def trader_node(state, name):
        company_name = state["company_of_interest"]
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
                    "Tens acesso a uma ferramenta get_atr_position_sizing que calcula o dimensionamento de posição "
                    "baseado na volatilidade ATR. Usa esta ferramenta SEMPRE que possível para obteres um "
                    "stop-loss e tamanho de posição baseados em dados reais de volatilidade, em vez de "
                    "estimativas arbitrárias. Para criptoativos, usa risk_percent=1.0 e atr_multiplier=2.0. "
                    "Para ações, usa risk_percent=1.0 e atr_multiplier=2.0."
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
                    f"Antes de finalizares, chama a ferramenta get_atr_position_sizing com o ticker='{company_name}', "
                    f"current_date='{current_date}', risk_percent=1.0, atr_multiplier=2.0 para obteres "
                    f"um dimensionamento de posição baseado em volatilidade real. Usa o resultado no campo "
                    f"position_sizing e para definir o stop_loss."
                ),
            },
        ]

        # First LLM call — may return tool calls for ATR sizing
        response = llm_with_tools.invoke(messages)

        # Process tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tc in response.tool_calls:
                if tc["name"] == "get_atr_position_sizing":
                    result = get_atr_position_sizing.invoke(tc["args"])
                    tool_results.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tc["id"],
                    ))

            if tool_results:
                messages.append(response)
                messages.extend(tool_results)

                # Final call with tool results — now produce structured output
                trader_plan = invoke_structured_or_freetext(
                    structured_llm,
                    llm,
                    messages,
                    render_trader_proposal,
                    "Trader",
                )
            else:
                trader_plan = invoke_structured_or_freetext(
                    structured_llm,
                    llm,
                    [messages[0], messages[1], response],
                    render_trader_proposal,
                    "Trader",
                )
        else:
            # No tool calls — produce structured output directly
            trader_plan = invoke_structured_or_freetext(
                structured_llm,
                llm,
                [messages[0], messages[1], response],
                render_trader_proposal,
                "Trader",
            )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
