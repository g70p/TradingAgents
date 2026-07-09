from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)

        trader_decision = state["trader_investment_plan"]

        prompt = f"""Enquanto Analista de Risco Conservador, o teu objetivo principal é proteger ativos, minimizar a volatilidade e garantir um crescimento estável e fiável. Priorizas a estabilidade, segurança e mitigação de risco, avaliando cuidadosamente perdas potenciais, recessões económicas e volatilidade do mercado. Ao avaliar a decisão ou plano do trader, examina criticamente os elementos de alto risco, apontando onde a decisão pode expor a empresa a riscos indevidos e onde alternativas mais cautelosas poderiam garantir ganhos de longo prazo. Aqui está a decisão do trader:

{trader_decision}

A tua tarefa é contrariar ativamente os argumentos dos analistas Agressivo e Neutro, destacando onde as suas visões podem ignorar ameaças potenciais ou não priorizar a sustentabilidade. Responde diretamente aos seus pontos, recorrendo às seguintes fontes de dados para construir um caso convincente para um ajustamento de baixo risco à decisão do trader:

{instrument_context}
Relatório de Análise de Mercado: {market_research_report}
Relatório de Sentimento nas Redes Sociais: {sentiment_report}
Relatório de Notícias Mundiais: {news_report}
Relatório de Fundamentais da Empresa: {fundamentals_report}
Aqui está o histórico atual da conversa: {history} Aqui está a última resposta do analista agressivo: {current_aggressive_response} Aqui está a última resposta do analista neutro: {current_neutral_response}. Se ainda não houver respostas dos outros pontos de vista, apresenta o teu próprio argumento com base nos dados disponíveis.

Participa ativamente, questionando o otimismo deles e enfatizando as potenciais desvantagens que podem ter ignorado. Responde a cada um dos seus contra-argumentos para demonstrar por que uma posição conservadora é, em última análise, o caminho mais seguro para os ativos da empresa. Foca-te em debater e criticar os argumentos deles para demonstrar a força de uma estratégia de baixo risco sobre as suas abordagens. Responde de forma conversacional, como se estivesses a falar, sem formatação especial.""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Conservador: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
