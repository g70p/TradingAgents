from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_indicators,
    get_instrument_context_from_state,
    get_language_instruction,
    get_stock_data,
    get_verified_market_snapshot,
)
from tradingagents.agents.utils.volume_framework import VOLUME_FRAMEWORK


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [
            get_stock_data,
            get_indicators,
            get_verified_market_snapshot,
        ]

        system_message = (
            """És um assistente de trading especializado em análise de mercados financeiros. A tua função é selecionar os **indicadores mais relevantes** para uma determinada condição de mercado ou estratégia de trading da lista abaixo. O objetivo é escolher até **8 indicadores** que forneçam informações complementares sem redundância. As categorias e os indicadores de cada categoria são:

Médias Móveis:
- close_50_sma: SMA 50: Um indicador de tendência de médio prazo. Utilização: Identificar a direção da tendência e servir como suporte/resistência dinâmica. Dicas: Tem atraso em relação ao preço; combinar com indicadores mais rápidos para sinais atempados.
- close_200_sma: SMA 200: Uma referência de tendência de longo prazo. Utilização: Confirmar a tendência geral do mercado e identificar formações de cruz dourada/da morte. Dicas: Reage lentamente; melhor para confirmação estratégica de tendência do que para entradas frequentes.
- close_10_ema: EMA 10: Uma média de curto prazo responsiva. Utilização: Capturar mudanças rápidas de momentum e potenciais pontos de entrada. Dicas: Propensa a ruído em mercados instáveis; usar com médias mais longas para filtrar sinais falsos.

Relacionados com MACD:
- macd: MACD: Calcula o momentum através de diferenças de EMAs. Utilização: Procurar cruzamentos e divergências como sinais de mudanças de tendência. Dicas: Confirmar com outros indicadores em mercados laterais ou de baixa volatilidade.
- macds: Sinal MACD: Uma suavização EMA da linha MACD. Utilização: Usar cruzamentos com a linha MACD para acionar operações. Dicas: Deve fazer parte de uma estratégia mais ampla para evitar falsos positivos.
- macdh: Histograma MACD: Mostra a diferença entre a linha MACD e o seu sinal. Utilização: Visualizar a força do momentum e detetar divergências antecipadamente. Dicas: Pode ser volátil; complementar com filtros adicionais em mercados rápidos.

Indicadores de Momentum:
- rsi: RSI: Mede o momentum para sinalizar condições de sobrecompra/sobrevenda. Utilização: Aplicar limiares 70/30 e observar divergências para sinalizar reversões. Dicas: Em tendências fortes, o RSI pode permanecer extremo; cruzar sempre com análise de tendência.

Indicadores de Volatilidade:
- boll: Banda Média de Bollinger: Uma SMA 20 que serve de base para as Bandas de Bollinger. Utilização: Atua como referência dinâmica para o movimento do preço. Dicas: Combinar com as bandas superior e inferior para identificar ruturas ou reversões.
- boll_ub: Banda Superior de Bollinger: Normalmente 2 desvios-padrão acima da linha média. Utilização: Sinaliza potenciais condições de sobrecompra e zonas de rutura. Dicas: Confirmar sinais com outras ferramentas; os preços podem viajar na banda em tendências fortes.
- boll_lb: Banda Inferior de Bollinger: Normalmente 2 desvios-padrão abaixo da linha média. Utilização: Indica potenciais condições de sobrevenda. Dicas: Usar análise adicional para evitar falsos sinais de reversão.
- atr: ATR: Mede a amplitude verdadeira média para quantificar a volatilidade. Utilização: Definir níveis de stop-loss e ajustar o tamanho das posições com base na volatilidade atual do mercado. Dicas: É uma medida reativa, por isso usa-a como parte de uma estratégia mais ampla de gestão de risco.

Indicadores Baseados em Volume:
- vwma: VWMA: Uma média móvel ponderada por volume. Utilização: Confirmar tendências integrando a ação do preço com dados de volume. Dicas: Atenção a resultados distorcidos por picos de volume; usar em combinação com outras análises de volume.

- Seleciona indicadores que forneçam informação diversa e complementar. Evita redundância (ex.: não seleciones tanto rsi como stochrsi). Explica também brevemente por que são adequados para o contexto de mercado em causa. Quando fizeres chamadas de ferramentas, usa o nome exato dos indicadores fornecidos acima, tal como estão definidos como parâmetros, caso contrário a chamada falhará. Certifica-te de chamar get_stock_data primeiro para obteres o CSV necessário para gerar os indicadores. Depois usa get_indicators com os nomes específicos dos indicadores.

Antes de escreveres o relatório final, chama get_verified_market_snapshot para este ticker e a data atual, e trata-o como a fonte de verdade para qualquer afirmação exata de valores OHLCV, níveis de preço ou indicadores. Se o resultado de outra ferramenta contradisser o snapshot verificado, assinala a discrepância em vez de inventar um número reconciliado. Não afirmes validação histórica, ressaltos de suporte/resistência ou variações percentuais exatas a menos que sejam diretamente sustentadas pelos resultados das ferramentas com datas e preços concretos.

⚠️ O snapshot inclui agora **Volume Relativo** e **Volatilidade Relativa** — rácios do dia atual vs média 20 dias. Usa estes dados para contextualizar se o movimento de hoje é significativo ou apenas ruído. Volume 2x acima da média → convicção alta. Volume 0.5x → ignora o sinal. Volatilidade 2x acima → stop loss mais largo. Volatilidade 0.5x → mercado adormecido, não forces entradas.

Escreve um relatório muito detalhado e matizado das tendências que observares. Fornece informações específicas e acionáveis com evidências de suporte para ajudar os traders a tomar decisões informadas."""
            + """ Certifica-te de anexar uma tabela Markdown no final do relatório para organizar os pontos-chave, de forma organizada e fácil de ler."""
            + """ Estrutura o teu relatório final obrigatoriamente assim:

## 1. Visão Geral — contexto imediato, tendência dominante, e o que o volume/volatilidade relativos indicam sobre a força do movimento atual.
## 2. Mapa Mental — árvore textual da análise.
## 3. Quadro de Sinais — tabela com indicadores, valores, sinal, interpretação. Inclui volume relativo e volatilidade relativa do snapshot.
## 4. Análise Detalhada — evidências, datas e preços concretos.
## 5. Riscos e Catalisadores — lista de riscos descendentes e catalisadores ascendentes.
## 6. Gate de Validação — checklist de integridade dos dados.
## 7. Notas de Continuidade — o que Bull/Bear/Trader precisam de saber."""
            + VOLUME_FRAMEWORK
            + get_language_instruction()
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
            "market_report": report,
        }

    return market_analyst_node
