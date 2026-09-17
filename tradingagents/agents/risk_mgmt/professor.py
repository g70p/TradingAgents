"""Agente Professor — Explicação simples para investidores ocasionais.


Recebe o relatório consolidado final e produz uma mensagem curta (3-4 parágrafos)
em português simples, sem jargão técnico, para entrega em canais como Telegram.

Objectivo: tornar a decisão de trading acessível a qualquer pessoa,
sem assumir conhecimento financeiro prévio.
"""


import re

from tradingagents.agents.utils.rating import RATING_REVIEW, extract_rating


def create_professor(llm):
    def professor_node(state) -> dict:
        ticker = state.get("company_of_interest", "N/D")
        trade_date = state.get("trade_date", "N/D")
        final_decision = state.get("final_trade_decision", "N/D")
        rating = extract_rating(final_decision)
        if rating is None or rating == RATING_REVIEW:
            return {
                "professor_message": (
                    f"⚠️ REVIEW — {ticker}, {trade_date}\n\n"
                    "## Análise\nA decisão final não contém uma classificação válida e coerente.\n\n"
                    "## Validação\nÉ necessário rever o relatório e os dados disponíveis.\n\n"
                    "## Ação\nNão foi emitida uma recomendação operacional."
                ),
                "messages": [],
            }
        asset_type = state.get("asset_type", "stock")

        # Gather all reports for context
        market_report = state.get("market_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        sentiment_report = state.get("sentiment_report", "")
        trader_plan = state.get("trader_investment_plan", "")
        risk = state.get("risk_debate_state", {}) or {}

        prompt = f"""És um explicador financeiro. A tua função é traduzir relatórios técnicos de trading para linguagem simples, como se estivesses a explicar a um amigo que não percebe de finanças.

REGRAS ABSOLUTAS:
1. Escreve SEMPRE em português europeu simples (PT-PT).
2. Usa o formato AVA (Análise → Validação → Ação) com os cabeçalhos ##.
3. Máximo 4 parágrafos curtos por secção. Cada parágrafo no máximo 3 frases.
4. Zero jargão técnico. NADA de "MACD", "RSI", "death cross", "HICP", "SMA", "Bollinger". Se precisares de falar de tendência, diz "o preço tem estado a subir/descer".
5. Começa com **Classificação**: {rating}. Mantém a classificação canónica exata.
6. Explica a decisão em termos práticos: "O que significa isto para o teu dinheiro?"
7. Menciona o risco principal em linguagem simples.
8. Termina com um emoji e uma frase curta de resumo.

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

Escreve a mensagem para Telegram seguindo este formato EXATO:

**Classificação**: {rating}
{ticker}, {trade_date}

## Análise
<2-3 frases simples: o que os dados mostram, tendência principal>

## Validação
<1-2 frases: confirmação com outras fontes, há contradições?>

## Ação
<2-3 frases: o que deves fazer, preços-alvo, stop loss, riscos>

<emoji final>
"""

        prompt += "\nQuantitativo:\n" + state.get("math_report", "")
        prompt += f"\nClassificação canónica: {rating}. Preserva-a, sem inventar preços ou níveis."
        response = llm.invoke(prompt)
        message = response.content.strip()
        # A second model must not change the signal or introduce new numeric levels.
        numeric = r"(?<!\w)\d+(?:[.,]\d+)*"
        evidence = "\n".join(str(state.get(key, "")) for key in (
            "final_trade_decision", "trader_investment_plan", "market_report",
            "fundamentals_report", "sentiment_report", "math_report", "trade_date",
        ))
        allowed = {n.replace(",", ".") for n in re.findall(numeric, evidence)}
        produced = {n.replace(",", ".") for n in re.findall(numeric, message)}
        if extract_rating(message) != rating or not produced <= allowed:
            message = (
                f"**Classificação**: {rating}\n{ticker}, {trade_date}\n\n"
                "## Análise\nA explicação automática não passou a verificação de coerência.\n\n"
                "## Validação\nA classificação foi preservada; não foram acrescentados níveis.\n\n"
                "## Ação\nRever o relatório original antes de interpretar a decisão."
            )

        return {
            "professor_message": message,
            "messages": [],
        }

    return professor_node
