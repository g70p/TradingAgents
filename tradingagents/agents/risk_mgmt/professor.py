"""Agente Professor — Explicação simples para investidores ocasionais.

Recebe o relatório consolidado final e produz uma mensagem curta (3-4 parágrafos)
em português simples, sem jargão técnico, para entrega em canais como Telegram.

Objectivo: tornar a decisão de trading acessível a qualquer pessoa,
sem assumir conhecimento financeiro prévio.
"""


def create_professor(llm):
    def professor_node(state) -> dict:
        ticker = state.get("company_of_interest", "N/D")
        trade_date = state.get("trade_date", "N/D")
        final_decision = state.get("final_trade_decision", "N/D")
        asset_type = state.get("asset_type", "stock")

        # Gather all reports for context
        market_report = state.get("market_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")
        trader_plan = state.get("trader_investment_plan", "")
        debate = state.get("investment_debate_state", {}) or {}
        risk = state.get("risk_debate_state", {}) or {}

        prompt = f"""És um explicador financeiro. A tua função é traduzir relatórios técnicos de trading para linguagem simples, como se estivesses a explicar a um amigo que não percebe de finanças.

REGRAS ABSOLUTAS:
1. Escreve SEMPRE em português europeu simples (PT-PT).
2. Máximo 4 parágrafos curtos. Cada parágrafo no máximo 3 frases.
3. Zero jargão técnico. NADA de "MACD", "RSI", "death cross", "HICP", "SMA", "Bollinger". Se precisares de falar de tendência, diz "o preço tem estado a subir/descer".
4. Começa SEMPRE com o emoji da decisão (🟢 BUY, 🔴 SELL, 🟡 HOLD) e o ticker + data.
5. Explica a decisão em termos práticos: "O que significa isto para o teu dinheiro?"
6. Menciona o risco principal em linguagem simples.
7. Termina com um emoji e uma frase curta de resumo.
8. NÃO uses Markdown. Apenas texto simples com emojis.

DECISÃO A EXPLICAR: {final_decision}
TICKER: {ticker}
DATA: {trade_date}
TIPO: {asset_type}

INFORMAÇÃO DE CONTEXTO (lê para perceberes, mas não copies):
Decisão final: {final_decision}
Plano do trader: {trader_plan[:800]}
Análise fundamental: {fundamentals_report[:400]}
Sentimento: {sentiment_report[:300]}
Mercado: {market_report[:300]}
Riscos: {str(risk.get('judge_decision', ''))[:300]}

Escreve a mensagem para Telegram AGORA:
"""

        response = llm.invoke(prompt)
        message = response.content.strip()

        return {
            "professor_message": message,
            "messages": [],
        }

    return professor_node
