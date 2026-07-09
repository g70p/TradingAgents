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
turn 0. Output uses the structured-output pattern (json_schema for
OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic), falling
back to free-text generation for providers that lack native support, so
the sentiment header (band + score + confidence) is deterministic across
runs and providers instead of free-form per-model prose.

See: https://github.com/TauricResearch/TradingAgents/issues/557
See: https://github.com/TauricResearch/TradingAgents/issues/796
"""

from datetime import datetime, timedelta

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.schemas import SentimentReport, render_sentiment_report
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
    get_news,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.dataflows.reddit import fetch_reddit_posts
from tradingagents.dataflows.stocktwits import fetch_stocktwits_messages


def _seven_days_back(trade_date: str) -> str:
    return (datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")


def create_sentiment_analyst(llm):
    """Create a sentiment analyst node for the trading graph.

    Pre-fetches news + StockTwits + Reddit data, injects them into the
    prompt as structured blocks, and produces a deterministic sentiment
    report via structured output (with a free-text fallback for providers
    that do not support it).
    """
    structured_llm = bind_structured(llm, SentimentReport, "Sentiment Analyst")

    def sentiment_analyst_node(state):
        ticker = state["company_of_interest"]
        end_date = state["trade_date"]
        start_date = _seven_days_back(end_date)
        instrument_context = get_instrument_context_from_state(state)

        # Pre-fetch all three sources. Each fetcher degrades gracefully and
        # returns a string (no exceptions surface from here), so the LLM
        # always sees something — either real data or a clear placeholder.
        news_block = get_news.func(ticker, start_date, end_date)
        stocktwits_block = fetch_stocktwits_messages(ticker, limit=30)
        reddit_block = fetch_reddit_posts(ticker)

        system_message = _build_system_message(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            news_block=news_block,
            stocktwits_block=stocktwits_block,
            reddit_block=reddit_block,
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

        report_text = invoke_structured_or_freetext(
            structured_llm,
            llm,
            formatted_messages,
            render_sentiment_report,
            "Sentiment Analyst",
        )

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
    stocktwits_block: str,
    reddit_block: str,
) -> str:
    """Assemble the sentiment-analyst system message with structured data blocks."""
    return f"""És um analista de sentimento de mercado financeiro. A tua tarefa é produzir um relatório de sentimento abrangente para {ticker}, cobrindo o período de {start_date} a {end_date}, com base em três fontes de dados complementares que já foram recolhidas para ti.

## Fontes de dados (pré-recolhidas, neste prompt)

### Títulos de notícias — Yahoo Finance, últimos 7 dias
Enquadramento institucional. Baseado em factos, sinal de movimento mais lento.

<start_of_news>
{news_block}
<end_of_news>

### Mensagens StockTwits — plataforma social de traders de retalho indexada por cashtag
Sinal de movimento rápido. Cada mensagem contém uma etiqueta de sentimento atribuída pelo utilizador (Bullish / Bearish / sem etiqueta) juntamente com o corpo da mensagem.

<start_of_stocktwits>
{stocktwits_block}
<end_of_stocktwits>

### Publicações do Reddit — r/wallstreetbets, r/stocks, r/investing (últimos 7 dias)
Discussão da comunidade. Sinal de envolvimento através da pontuação de upvotes e contagem de comentários. O caráter do subreddit importa (r/wallstreetbets é frequentemente contrário/eufórico; r/stocks mais comedido; r/investing de mais longo prazo).

<start_of_reddit>
{reddit_block}
<end_of_reddit>

## Como analisar estes dados (melhores práticas)

1. **Lê o rácio Bullish/Bearish do StockTwits como um sinal líder de sentimento de retalho.** Uma divisão 70/30 bullish/bearish é moderadamente bullish; ≥90/10 pode indicar sobre-extensão e risco contrário; 50/50 é incerteza. O tamanho da amostra importa — baseia as proporções na contagem real de mensagens, não apenas em percentagens.

2. **Procura divergências entre fontes.** Se o enquadramento das notícias é bearish mas o StockTwits é esmagadoramente bullish, esse desalinhamento é em si um sinal — pode significar que o retalho está a apostar numa tese que o fluxo de notícias ainda não captou (ou vice-versa, que o retalho está a perseguir enquanto os institucionais estão cautelosos).

3. **Pondera as publicações do Reddit pelo envolvimento.** Um tópico com 400 upvotes / 200 comentários reflete atenção da comunidade; uma publicação com 3 upvotes é ruído. Lê os excertos do corpo para contexto — o título sozinho muitas vezes engana.

4. **Distingue opinião de evento.** Um título de notícia ("Nvidia anuncia acordo de 500M com a Corning") é um evento; uma publicação no StockTwits ("a comprar NVDA, isto vai disparar") é opinião. Ambos são inputs mas devem ser ponderados de forma diferente nas tuas conclusões.

5. **Identifica temas narrativos recorrentes.** Que tópico aparece repetidamente em várias fontes? Essa é a narrativa dominante que está a impulsionar o sentimento atual.

6. **Sê honesto sobre as limitações dos dados.** Se o StockTwits devolveu apenas um punhado de mensagens, ou se uma ou mais fontes devolveram um placeholder "<indisponível>", a leitura de sentimento é menos robusta — assinala isto explicitamente no campo `confidence` e na narrativa. Se as fontes estão silenciosas sobre um determinado subreddit, diz isso.

7. **Identifica catalisadores e riscos** que emergem das várias fontes — notícias de próximos resultados, lançamentos de produtos, ameaças competitivas, manchetes macro, etc.

8. **Sentimento passado não é preditivo.** Enquadra as tuas conclusões como sinal para o trader ponderar juntamente com fundamentais e técnicos, não como uma previsão de preço.

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
