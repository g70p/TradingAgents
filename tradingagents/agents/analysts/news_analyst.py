from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_instrument_context_from_state,
    get_language_instruction,
    get_macro_indicators,
    get_news,
    get_prediction_markets,
)


def create_news_analyst(llm):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        asset_type = state.get("asset_type", "stock")
        asset_label = "empresa" if asset_type == "stock" else "ativo"
        instrument_context = get_instrument_context_from_state(state)

        tools = [
            get_news,
            get_global_news,
            get_macro_indicators,
            get_prediction_markets,
        ]

        system_message = (
            f"És um investigador de notícias encarregado de analisar notícias e tendências recentes da última semana. Por favor, escreve um relatório abrangente do estado atual do mundo que seja relevante para trading e macroeconomia. Usa as ferramentas disponíveis: get_news(ticker, start_date, end_date) para pesquisas de notícias específicas sobre a {asset_label} por símbolo, get_global_news(curr_date, look_back_days, limit) para notícias macroeconómicas mais amplas, get_macro_indicators(indicator, curr_date, look_back_days) para fundamentar o comentário macroeconómico em dados reais do FRED (ex.: 'cpi', 'core_pce', 'unemployment', 'fed_funds_rate', '10y_treasury', 'yield_curve'), e get_prediction_markets(topic, limit) para probabilidades em tempo real de eventos futuros implícitas no mercado (ex.: 'Fed rate cut', 'recession 2026', eventos geopolíticos ou setoriais). Fornece informações específicas e acionáveis com evidências de suporte para ajudar os traders a tomar decisões informadas."
            + """ Certifica-te de anexar uma tabela Markdown no final do relatório para organizar os pontos-chave, de forma organizada e fácil de ler."""
            + get_language_instruction() + "\n\nEstrutura o teu relatorio final obrigatoriamente com estas seccoes:\n## 1. Visao Geral da Cobertura Noticiosa\n## 2. Mapa Mental das Fontes\n## 3. Quadro de Sinais Macro (tabela)\n## 4. Analise Detalhada\n## 5. Mercados de Previsao\n## 6. Riscos e Catalisadores\n## 7. Gate de Validacao"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "És um assistente de IA útil, a colaborar com outros assistentes."
                    " Usa as ferramentas fornecidas para progredir na resposta à questão."
                    " Se não conseguires responder completamente, não há problema; outro assistente com ferramentas diferentes"
                    " ajudará onde paraste. Executa o que puderes para fazer progresso."
                    " Se tu ou qualquer outro assistente tiver a PROPOSTA FINAL DE TRANSAÇÃO: **COMPRAR/MANTER/VENDER** ou produto final,"
                    " prefixa a tua resposta com PROPOSTA FINAL DE TRANSAÇÃO: **COMPRAR/MANTER/VENDER** para a equipa saber que deve parar."
                    " Tens acesso às seguintes ferramentas: {tool_names}."
                    " A data de hoje é {current_date}; trata-a como 'agora' para toda a análise e intervalos de datas das ferramentas. {instrument_context}\n"
                    "{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
