from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

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

        prompt = f"""És um Analista Touro (Bull) a defender o investimento na {target_label}. A tua tarefa é construir um caso forte, baseado em evidências, que enfatize o potencial de crescimento, vantagens competitivas e indicadores de mercado positivos. Utiliza a investigação e os dados fornecidos para responder a preocupações e contrariar argumentos bearish de forma eficaz.

Pontos-chave a focar:
- Potencial de Crescimento: Destaca as oportunidades de mercado da empresa, projeções de receitas e escalabilidade.
- Vantagens Competitivas: Enfatiza fatores como produtos únicos, marca forte ou posicionamento dominante no mercado.
- Indicadores Positivos: Usa saúde financeira, tendências do setor e notícias positivas recentes como evidência.
- Contra-argumentos ao Urso: Analisa criticamente o argumento bearish com dados específicos e raciocínio sólido, respondendo às preocupações de forma aprofundada e mostrando por que a perspetiva bull tem maior mérito.
- Envolvimento: Apresenta o teu argumento num estilo conversacional, interagindo diretamente com os pontos do analista bear e debatendo eficazmente em vez de apenas listar dados.

Recursos disponíveis:
{instrument_context}
Relatório de análise de mercado: {market_research_report}
Relatório de sentimento nas redes sociais: {sentiment_report}
Notícias mundiais mais recentes: {news_report}
{fundamentals_label}: {fundamentals_report}
Histórico da conversa do debate: {history}
Último argumento do urso: {current_response}
Usa esta informação para apresentar um argumento bull convincente, refutar as preocupações do urso e participar num debate dinâmico que demonstre os pontos fortes da posição bull.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Touro: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
