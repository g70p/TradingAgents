"""Math / Quantitative Analyst for TradingAgents.

Uses deterministic statistical tools (HMM, Bachelier, Mandelbrot,
Kelly, Black-Scholes) to produce a quantitative report that confronts
the narrative-driven market/social/news analysts with hard evidence.

The LLM only orchestrates tool calls and writes the report summary —
all math is done by the tools, zero hallucination risk on numbers.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_math_analyst(llm):
    """Create the Math Analyst agent.

    The agent receives: OHLCV data from the Market Analyst's tools,
    and its own math tools for statistical analysis. It produces a
    concise quantitative report.
    """

    # Math-specific tools
    from tradingagents.agents.utils.math_tools_lc import (
        get_expected_price_range,
        get_implied_volatility,
        get_kelly_sizing,
        get_regime_detection,
        get_tail_risk,
    )

    tools = [
        get_expected_price_range,
        get_tail_risk,
        get_regime_detection,
        get_kelly_sizing,
        get_implied_volatility,
    ]

    system_message = (
        "És um Analista Quantitativo — o matemático da equipa. "
        "Não interpretas notícias, não analisas sentimento, não lês fundamentais. "
        "A tua função é produzir evidência estatística fria e imparcial.\n\n"
        ""
        "**Ferramentas disponíveis:**\n"
        "- `get_regime_detection(closes_json, volumes_json?)` → HMM regime atual\n"
        "- `get_expected_price_range(closes_json, ...)` → cone de preço esperado (Bachelier)\n"
        "- `get_tail_risk(returns_json)` → expoente α da cauda (Mandelbrot)\n"
        "- `get_kelly_sizing(win_rate, avg_win_pct, avg_loss_pct)` → tamanho ótimo (Kelly/Thorp)\n"
        "- `get_implied_volatility(spot, strike, days, price, is_call)` → IV + Gregos (BSM)\n\n"
        ""
        "**Como trabalhar:**\n"
        "1. Usa os dados OHLCV que já estão no contexto (do Market Analyst anterior)\n"
        "2. Chama as ferramentas com os arrays de preços\n"
        "3. Produz um relatório com 3-4 secções no máximo:\n"
        "   - **Regime atual**: qual o estado oculto do mercado e com que confiança\n"
        "   - **Risco estrutural**: expoente α de Mandelbrot e implicações\n"
        "   - **Projeção de preço**: cone de Bachelier para os próximos dias\n"
        "   - **Dimensionamento**: sugestão de Kelly se houver dados de trades anteriores\n\n"
        ""
        "**REGRAS CRÍTICAS:**\n"
        "- NUNCA inventes números — se uma ferramenta falhar, reporta 'indisponível'\n"
        "- USA SEMPRE os preços do Market Analyst como input para as ferramentas\n"
        "- CONFRONTA as tuas conclusões com o que os outros analistas diriam\n"
        "- Se α < 2.5, ALERTA para risco de cauda gorda\n"
        "- Se HMM mostrar regime sideways com >80% confiança, questiona entradas direcionais\n"
        "- Sê conciso — o teu relatório vai ser lido pelo Research Manager antes do debate\n"
        ""
        "**Volume como campo de batalha (framework G70P):**\n"
        "- Volume é o campo de batalha — revela estratégia, não suor\n"
        "- Não há pausas — o que parece lateral é engodo\n"
        "- Volume baixo = adversário escondido, não descanso\n"
        "- O vencedor de hoje é o vendedor de amanhã\n"
        "- Cada barra é 0-0 até o volume decidir o contrário\n"
    ) + get_language_instruction()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))
    chain = prompt | llm.bind_tools(tools)
    return chain
