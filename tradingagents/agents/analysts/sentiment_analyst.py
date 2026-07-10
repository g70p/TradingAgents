"""Sentiment analyst — multi-source sentiment analysis for a target ticker.

Previously named ``social_media_analyst``. Renamed and redesigned because
the old version had a prompt that demanded social-media analysis but the
only tool available was Yahoo Finance news — which led LLMs to fabricate
Reddit/X/StockTwits content under prompt pressure (verified live).

The redesigned agent pre-fetches three complementary data sources before
the LLM is invoked and injects them into the prompt as structured blocks:

  1. News headlines     — Yahoo Finance (institutional framing)
  2. StockTwits messages — retail-trader posts indexed by cashtag, with
                           user-labeled Bullish/Bearish sentiment tags
  3. Reddit posts        — r/wallstreetbets, r/stocks, r/investing

The agent does not use tool-calling; the data is in the prompt from
turn 0. Output is free-text markdown — no structured-output wrapper,
no fallback warnings.

See: https://github.com/TauricResearch/TradingAgents/issues/557
See: https://github.com/TauricResearch/TradingAgents/issues/796
"""

from datetime import datetime, timedelta

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
    get_news,
)
from tradingagents.dataflows.google_news import fetch_google_news_sentiment
from tradingagents.dataflows.news_aggregator import fetch_news_multi_source


def _seven_days_back(trade_date: str) -> str:
    return (datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")


def create_sentiment_analyst(llm):
    """Create a sentiment analyst node for the trading graph.

    Pre-fetches news + StockTwits + Reddit data, injects them into the
    prompt as structured blocks, and produces a deterministic sentiment
    report via structured output (with a free-text fallback for providers
    that do not support it).
    """
    def sentiment_analyst_node(state):
        ticker = state["company_of_interest"]
        end_date = state["trade_date"]
        start_date = _seven_days_back(end_date)
        instrument_context = get_instrument_context_from_state(state)

        # Pre-fetch all three sources. Each fetcher degrades gracefully and
        # returns a string (no exceptions surface from here), so the LLM
        # always sees something — either real data or a clear placeholder.
        news_block = get_news.func(ticker, start_date, end_date)
        google_block = fetch_google_news_sentiment(ticker, limit=12)
        # Multi-source aggregator as adicional source (Euronext, Investing, CNBC...)
        extra_block = fetch_news_multi_source(ticker, limit_per_source=4)

        system_message = _build_system_message(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            news_block=news_block,
            google_block=google_block,
            extra_block=extra_block,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "És um assistente de IA útil, a colaborar com outros assistentes."
                    " Se tu ou qualquer outro assistente tiver a PROPOSTA FINAL DE TRANSAÇÃO: **COMPRAR/MANTER/VENDER** ou produto final,"
                    " prefixa a tua resposta com PROPOSTA FINAL DE TRANSAÇÃO: **COMPRAR/MANTER/VENDER** para a equipa saber que deve parar."
                    " A data de hoje é {current_date}; trata-a como 'agora' para toda a análise e intervalos de datas das ferramentas. {instrument_context}"
                    "\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=end_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        # Format the template into a concrete message list so the structured
        # and free-text paths receive the same input. No bind_tools — the
        # data is already in the prompt.
        formatted_messages = prompt.format_messages(messages=state["messages"])

        response = llm.invoke(formatted_messages)
        report_text = str(response.content) if hasattr(response, 'content') else str(response)

        return {
            "messages": [AIMessage(content=report_text)],
            "sentiment_report": report_text,
        }

    return sentiment_analyst_node


def _build_system_message(
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    news_block: str,
    google_block: str,
    extra_block: str,
) -> str:
    """Assemble the sentiment-analyst system message with structured data blocks."""
    return f"""És um analista de sentimento de mercado financeiro. A tua tarefa é produzir um relatório de sentimento abrangente para {ticker}, cobrindo o período de {start_date} a {end_date}, com base em fontes de dados complementares que já foram recolhidas para ti.

**⚠️ FORMATO OBRIGATÓRIO — AVA ⚠️**
Toda a tua resposta DEVE seguir o método AVA (Análise → Validação → Ação).

## Fontes de dados (pré-recolhidas, neste prompt)

### Notícias via Yahoo Finance, últimos 7 dias
Enquadramento institucional. Baseado em factos, sinal de movimento mais lento.

<start_of_yahoo_news>
{news_block}
<end_of_yahoo_news>

### Notícias via Google News (PT + EN)
Cobertura alargada de fontes noticiosas. Inclui imprensa portuguesa e internacional. Manchetes de múltiplas fontes para uma visão diversificada do sentimento mediático.

<start_of_google_news>
{google_block}
<end_of_google_news>

### Fontes Internacionais Agregadas (Euronext, Investing.com, CNBC, MarketWatch)
Cobertura multi-fonte de mercados globais. Inclui comunicados oficiais de bolsas europeias, imprensa financeira internacional, e análise de mercados.

<start_of_extra>
{extra_block}
<end_of_extra>

## Como analisar estes dados (melhores práticas)

1. **Lê as manchetes do Yahoo Finance como sinal institucional.** São factuais, de movimento mais lento, focadas em resultados, regulação e adoção.

2. **Usa o Google News para sentir o tom mediático geral.** As manchetes refletem o enquadramento que o público geral está a receber. Se as manchetes são consistentemente negativas, o sentimento de retalho tende a seguir.

3. **Procura divergências entre as duas fontes.** Se o Yahoo Finance está neutro mas o Google News está repleto de manchetes alarmistas, isso é um sinal de que o sentimento de retalho pode estar em pânico — ou vice-versa.

4. **Distingue opinião de evento.** Uma notícia institucional ("BCE mantém taxas") é um evento; uma manchete do Google News ("Mercados em pânico com decisão do BCE") é enquadramento. Ambos são inputs mas devem ser ponderados de forma diferente.

5. **Identifica temas narrativos recorrentes.** Que tópico aparece repetidamente em várias fontes? Essa é a narrativa dominante que está a impulsionar o sentimento atual.

6. **Sê honesto sobre as limitações dos dados.** Se uma das fontes devolveu poucos resultados ou um placeholder "<indisponível>", a leitura de sentimento é menos robusta — assinala isto explicitamente no campo `confidence` e na narrativa.

7. **Identifica catalisadores e riscos** que emergem das várias fontes — notícias de resultados, lançamentos de produtos, decisões de bancos centrais, tensões geopolíticas.

8. **Sentimento passado não é preditivo.** Enquadra as tuas conclusões como sinal para o trader ponderar juntamente com fundamentais e técnicos, não como uma previsão de preço.

## AVA — Análise, Validação, Ação
- **Análise**: <síntese dos sinais de sentimento das várias fontes; tendência dominante>
- **Validação**: <cross-check entre fontes; há divergências? o Google News contradiz o Yahoo Finance?>
- **Ação**: <recomendação de sentimento final: overall_band + overall_score + confidence>

## Campos de saída

Preenche os seguintes campos:

- **overall_band**: Exatamente um de: Bullish / Mildly Bullish / Neutral / Mixed / Mildly Bearish / Bearish. Usa Mixed quando as fontes apontam em direções claramente diferentes; Neutral apenas quando todas as fontes estão genuinamente silenciosas.
- **overall_score**: Um número de 0 (máximo bearish) a 10 (máximo bullish); 5 é neutro. Mantém-no consistente com o overall_band.
- **confidence**: low / medium / high, com base na qualidade dos dados e tamanho da amostra.
- **narrative**: Análise completa fonte a fonte, divergências, temas narrativos dominantes, catalisadores e riscos, e uma tabela resumo em markdown dos principais sinais de sentimento (direção, fonte, evidência de suporte).

{get_language_instruction()}"""


# ---------------------------------------------------------------------------
# Backwards-compatibility shim
# ---------------------------------------------------------------------------
def create_social_media_analyst(llm):
    """Deprecated alias for :func:`create_sentiment_analyst`.

    Kept so existing code that imports ``create_social_media_analyst``
    continues to work.

    .. deprecated::
        Import :func:`create_sentiment_analyst` directly instead.
    """
    import warnings
    warnings.warn(
        "create_social_media_analyst is deprecated and will be removed in a "
        "future version. Use create_sentiment_analyst instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return create_sentiment_analyst(llm)
