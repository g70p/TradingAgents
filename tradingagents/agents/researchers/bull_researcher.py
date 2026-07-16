from tradingagents.agents.utils.agent_utils import (
    get_language_instruction,
)
from tradingagents.agents.utils.report_consolidator import consolidate_analyst_reports
from tradingagents.agents.utils.volume_framework import VOLUME_FRAMEWORK



def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")
        current_response = investment_debate_state.get("current_response", "")
        asset_type = state.get("asset_type", "stock")
        target_label = "ação" if asset_type == "stock" else "ativo"
        trade_date = state["trade_date"]
        ticker = state.get("company_of_interest", "N/D")

        # Consolidate all 4 analyst reports into a single AVA-structured document
        consolidated = consolidate_analyst_reports(
            market_report=state.get("market_report", ""),
            sentiment_report=state.get("sentiment_report", ""),
            news_report=state.get("news_report", ""),
            fundamentals_report=state.get("fundamentals_report", ""),
            ticker=ticker,
            trade_date=trade_date,
        )

        prompt = f"""És um Analista Touro (Bull) a defender o investimento na {target_label}. A tua tarefa é construir um caso forte, baseado em evidências, que enfatize o potencial de crescimento, vantagens competitivas e indicadores de mercado positivos.

Recebeste um RELATÓRIO CONSOLIDADO que unifica as análises de 4 especialistas independentes. Usa-o como a tua única fonte de dados.

Estrutura da tua resposta (obrigatório):

## 1. Visão Geral Bull
Resumo executivo do teu caso de investimento — o que torna esta {target_label} atrativa AGORA.

## 2. Mapa Mental do Caso Bull
```
Caso Bull — {ticker}
├── Catalisador Principal
├── Vantagens Competitivas
├── Indicadores Positivos
└── Refutação de Riscos
```

## 3. Análise Baseada em Evidências
Usa dados concretos do relatório consolidado para sustentar cada ponto.

## 4. Refutação do Argumento Urso
Se houver argumento bear prévio, responde ponto por ponto com contra-evidências.

## 5. Gate de Validação
- [ ] Todos os argumentos baseiam-se em dados do relatório consolidado.
- [ ] Nenhum valor foi inventado.
- [ ] As refutações são específicas e baseadas em evidências.

## 6. Notas para o Debate
O que o Urso e o Gestor de Investigação precisam de saber.

---

### RELATÓRIO CONSOLIDADO (fonte única de verdade):
{consolidated}

### Histórico do debate:
{history}

### Último argumento do urso:
{current_response}

Usa esta informação para apresentar um argumento bull convincente, refutar as preocupações do urso e participar num debate dinâmico.
""" + VOLUME_FRAMEWORK + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Analista Touro:\n{response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
