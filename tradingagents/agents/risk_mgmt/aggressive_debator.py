from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)

        trader_decision = state["trader_investment_plan"]

        prompt = f"""Enquanto Analista de Risco Agressivo, a tua função é defender ativamente oportunidades de alta recompensa e alto risco, enfatizando estratégias arrojadas e vantagens competitivas. Ao avaliar a decisão ou plano do trader, concentra-te intensamente no potencial de valorização, crescimento e benefícios inovadores — mesmo quando estes acarretam risco elevado. Usa os dados de mercado e a análise de sentimento fornecidos para fortalecer os teus argumentos e desafiar as visões opostas. Especificamente, responde diretamente a cada ponto levantado pelos analistas conservador e neutro, contra-argumentando com refutações baseadas em dados e raciocínio persuasivo. Destaca onde a cautela deles pode perder oportunidades cruciais ou onde os seus pressupostos podem ser excessivamente conservadores. Aqui está a decisão do trader:

{trader_decision}

A tua tarefa é criar um caso convincente para a decisão do trader, questionando e criticando as posições conservadora e neutra para demonstrar por que a tua perspetiva de alta recompensa oferece o melhor caminho a seguir. Incorpora informações das seguintes fontes nos teus argumentos:

{instrument_context}
Relatório de Análise de Mercado: {market_research_report}
Relatório de Sentimento nas Redes Sociais: {sentiment_report}
Relatório de Notícias Mundiais: {news_report}
Relatório de Fundamentais da Empresa: {fundamentals_report}
Aqui está o histórico atual da conversa: {history} Aqui estão os últimos argumentos do analista conservador: {current_conservative_response} Aqui estão os últimos argumentos do analista neutro: {current_neutral_response}. Se ainda não houver respostas dos outros pontos de vista, apresenta o teu próprio argumento com base nos dados disponíveis.

Participa ativamente, respondendo a quaisquer preocupações específicas levantadas, refutando as fraquezas na lógica deles e afirmando os benefícios de assumir riscos para superar as normas do mercado. Mantém o foco em debater e persuadir, não apenas em apresentar dados. Desafia cada contra-argumento para sublinhar por que uma abordagem de alto risco é a ideal. Responde de forma conversacional, como se estivesses a falar, sem formatação especial.""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Agressivo: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
