from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
        ]

        system_message = (
            "És um investigador encarregado de analisar a informação fundamental da última semana sobre uma empresa. Por favor, escreve um relatório abrangente da informação fundamental da empresa, como documentos financeiros, perfil da empresa, fundamentos financeiros básicos e histórico financeiro, para obteres uma visão completa da informação fundamental da empresa e informares os traders. Certifica-te de incluir o máximo de detalhe possível. Fornece informações específicas e acionáveis com evidências de suporte para ajudar os traders a tomar decisões informadas."
            + " Certifica-te de anexar uma tabela Markdown no final do relatório para organizar os pontos-chave, de forma organizada e fácil de ler."
            + " Usa as ferramentas disponíveis: `get_fundamentals` para análise abrangente da empresa, `get_balance_sheet`, `get_cashflow` e `get_income_statement` para demonstrações financeiras específicas."
            + get_language_instruction() + "\n\nEstrutura o teu relatorio final obrigatoriamente com estas seccoes:\n## 1. Visao Geral Fundamental\n## 2. Mapa Mental dos Indicadores\n## 3. Quadro de Racios e Metricas (tabela)\n## 4. Analise Detalhada\n## 5. Posicionamento na Faixa de 52 Semanas\n## 6. Riscos e Catalisadores\n## 7. Gate de Validacao",
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
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
