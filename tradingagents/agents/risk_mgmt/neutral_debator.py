from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)

        trader_decision = state["trader_investment_plan"]

        prompt = f"""Enquanto Analista de Risco Neutro, a tua função é fornecer uma perspetiva equilibrada, ponderando tanto os potenciais benefícios como os riscos da decisão ou plano do trader. Priorizas uma abordagem bem ponderada, avaliando os pontos positivos e negativos enquanto consideras tendências de mercado mais amplas, potenciais mudanças económicas e estratégias de diversificação. Aqui está a decisão do trader:

{trader_decision}

A tua tarefa é desafiar tanto o Analista Agressivo como o Conservador, apontando onde cada perspetiva pode ser excessivamente otimista ou excessivamente cautelosa. Usa informações das seguintes fontes de dados para apoiar uma estratégia moderada e sustentável para ajustar a decisão do trader:

{instrument_context}
Relatório de Análise de Mercado: {market_research_report}
Relatório de Sentimento nas Redes Sociais: {sentiment_report}
Relatório de Notícias Mundiais: {news_report}
Relatório de Fundamentais da Empresa: {fundamentals_report}
Aqui está o histórico atual da conversa: {history} Aqui está a última resposta do analista agressivo: {current_aggressive_response} Aqui está a última resposta do analista conservador: {current_conservative_response}. Se ainda não houver respostas dos outros pontos de vista, apresenta o teu próprio argumento com base nos dados disponíveis.

Participa ativamente, analisando ambos os lados de forma crítica, abordando as fraquezas nos argumentos agressivo e conservador para defender uma abordagem mais equilibrada. Desafia cada um dos seus pontos para ilustrar por que uma estratégia de risco moderado pode oferecer o melhor dos dois mundos, proporcionando potencial de crescimento enquanto protege contra a volatilidade extrema. Foca-te em debater em vez de simplesmente apresentar dados, procurando mostrar que uma visão equilibrada pode conduzir aos resultados mais fiáveis. Responde de forma conversacional, como se estivesses a falar, sem formatação especial.""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Neutro: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
