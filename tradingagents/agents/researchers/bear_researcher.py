from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_bear_researcher(llm):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)
        asset_type = state.get("asset_type", "stock")
        target_label = "ação" if asset_type == "stock" else "ativo"
        fundamentals_label = (
            "Relatório de fundamentais da empresa"
            if asset_type == "stock"
            else "Relatório de fundamentais do ativo (pode estar indisponível para cripto)"
        )

        prompt = f"""És um Analista Urso (Bear) a defender o caso contra o investimento na {target_label}. O teu objetivo é apresentar um argumento bem fundamentado que enfatize riscos, desafios e indicadores negativos. Utiliza a investigação e os dados fornecidos para destacar potenciais desvantagens e contrariar argumentos bullish de forma eficaz.

Pontos-chave a focar:

- Riscos e Desafios: Destaca fatores como saturação do mercado, instabilidade financeira ou ameaças macroeconómicas que possam prejudicar o desempenho da ação.
- Fraquezas Competitivas: Enfatiza vulnerabilidades como posicionamento de mercado mais fraco, inovação em declínio ou ameaças de concorrentes.
- Indicadores Negativos: Usa evidências de dados financeiros, tendências de mercado ou notícias adversas recentes para sustentar a tua posição.
- Contra-argumentos ao Touro: Analisa criticamente o argumento bull com dados específicos e raciocínio sólido, expondo fraquezas ou pressupostos excessivamente otimistas.
- Envolvimento: Apresenta o teu argumento num estilo conversacional, interagindo diretamente com os pontos do analista bull e debatendo eficazmente em vez de simplesmente listar factos.

Recursos disponíveis:

{instrument_context}
Relatório de análise de mercado: {market_research_report}
Relatório de sentimento nas redes sociais: {sentiment_report}
Notícias mundiais mais recentes: {news_report}
{fundamentals_label}: {fundamentals_report}
Histórico da conversa do debate: {history}
Último argumento do touro: {current_response}
Usa esta informação para apresentar um argumento bear convincente, refutar as afirmações do touro e participar num debate dinâmico que demonstre os riscos e fraquezas de investir na {target_label}.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Urso: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
