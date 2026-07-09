"""Pydantic schemas used by agents that produce structured output.

The framework's primary artifact is still prose: each agent's natural-language
reasoning is what users read in the saved markdown reports and what the
downstream agents read as context.  Structured output is layered onto the
three decision-making agents (Research Manager, Trader, Portfolio Manager)
so that:

- Their outputs follow consistent section headers across runs and providers
- Each provider's native structured-output mode is used (json_schema for
  OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic)
- Schema field descriptions become the model's output instructions, freeing
  the prompt body to focus on context and the rating-scale guidance
- A render helper turns the parsed Pydantic instance back into the same
  markdown shape the rest of the system already consumes, so display,
  memory log, and saved reports keep working unchanged
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# LLMs sometimes write a placeholder string ("None", "N/A", ...) into an optional
# numeric field instead of omitting it. Coerce those to None so the structured
# call validates instead of erroring (#1058). Pydantic still parses real numeric
# strings ("189.5") to float.
_NULLISH_FLOAT = {"", "none", "n/a", "na", "null", "nil", "-", "tbd", "unknown"}


def _coerce_optional_float(value):
    if isinstance(value, str) and value.strip().lower() in _NULLISH_FLOAT:
        return None
    return value


# ---------------------------------------------------------------------------
# Shared rating types
# ---------------------------------------------------------------------------


class PortfolioRating(str, Enum):
    """Escala de 5 níveis usada pelo Gestor de Investigação e Gestor de Portfólio."""

    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"


class TraderAction(str, Enum):
    """Direção de transação de 3 níveis usada pelo Trader.

    A função do Trader é traduzir o plano de investimento do Gestor de Investigação
    numa proposta de transação concreta: deve a mesa executar uma Compra, uma
    Venda, ou Manter nesta ronda. O dimensionamento de posição e as chamadas
    matizadas de Sobreponderar / Subponderar acontecem depois no Gestor de Portfólio.
    """

    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


# ---------------------------------------------------------------------------
# Research Manager
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Plano de investimento estruturado produzido pelo Gestor de Investigação.

    Passagem ao Trader: a recomendação fixa a visão direcional,
    a fundamentação captura qual lado do debate touro/urso prevaleceu,
    e as ações estratégicas traduzem isso em instruções concretas
    que o trader pode executar.
    """

    recommendation: PortfolioRating = Field(
        description=(
            "A recomendação de investimento. Exatamente uma de: Buy / Overweight / "
            "Hold / Underweight / Sell. Reserva Hold para situações em que as "
            "evidências de ambos os lados estão genuinamente equilibradas; caso "
            "contrário, compromete-te com o lado que tiver os argumentos mais fortes."
        ),
    )
    rationale: str = Field(
        description=(
            "Resumo conversacional dos pontos-chave de ambos os lados do "
            "debate, terminando com quais argumentos levaram à recomendação. "
            "Fala naturalmente, como se fosse para um colega de equipa."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Passos concretos para o trader implementar a recomendação, "
            "incluindo orientação de dimensionamento de posição consistente com a classificação."
        ),
    )


def render_research_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan to markdown for storage and the trader's prompt context."""
    return "\n".join([
        f"**Recomendação**: {plan.recommendation.value}",
        "",
        f"**Fundamentação**: {plan.rationale}",
        "",
        f"**Ações Estratégicas**: {plan.strategic_actions}",
    ])


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Proposta de transação estruturada produzida pelo Trader.

    O trader lê o plano de investimento do Gestor de Investigação e os relatórios
    dos analistas, depois transforma-os numa transação concreta: que ação tomar,
    o raciocínio que a justifica, e os níveis práticos para
    entrada, stop-loss e dimensionamento.
    """

    action: TraderAction = Field(
        description="A direção da transação. Exatamente uma de: Buy / Hold / Sell.",
    )
    reasoning: str = Field(
        description=(
            "O caso para esta ação, ancorado nos relatórios dos analistas e "
            "no plano de investigação. Duas a quatro frases."
        ),
    )
    entry_price: float | None = Field(
        default=None,
        description="Preço de entrada alvo opcional, na moeda de cotação do instrumento.",
    )
    stop_loss: float | None = Field(
        default=None,
        description="Preço de stop-loss opcional, na moeda de cotação do instrumento.",
    )
    position_sizing: str | None = Field(
        default=None,
        description="Orientação de dimensionamento opcional, ex.: '5% do portfólio'.",
    )

    @field_validator("entry_price", "stop_loss", mode="before")
    @classmethod
    def _nullish_float_to_none(cls, v):
        return _coerce_optional_float(v)


def render_trader_proposal(proposal: TraderProposal) -> str:
    """Render a TraderProposal to markdown.

    The trailing ``FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`` line is
    preserved for backward compatibility with the analyst stop-signal text
    and any external code that greps for it.
    """
    parts = [
        f"**Ação**: {proposal.action.value}",
        "",
        f"**Raciocínio**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Preço de Entrada**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Dimensionamento de Posição**: {proposal.position_sizing}"])
    parts.extend([
        "",
        f"PROPOSTA FINAL DE TRANSAÇÃO: **{proposal.action.value.upper()}**",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Resultado estruturado produzido pelo Gestor de Portfólio.

    O modelo preenche cada campo como parte da sua chamada LLM principal; nenhuma
    passagem de extração separada é necessária. As descrições dos campos funcionam
    como instruções de saída do modelo, por isso o corpo do prompt só precisa de
    transmitir contexto e a orientação da escala de classificação.
    """

    rating: PortfolioRating = Field(
        description=(
            "A classificação final da posição. Exatamente uma de: Buy / Overweight / Hold / "
            "Underweight / Sell, escolhida com base no debate dos analistas."
        ),
    )
    executive_summary: str = Field(
        description=(
            "Um plano de ação conciso cobrindo estratégia de entrada, dimensionamento "
            "de posição, níveis-chave de risco e horizonte temporal. Duas a quatro frases."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Raciocínio detalhado ancorado em evidências específicas do debate dos "
            "analistas. Se lições anteriores forem referenciadas no contexto do prompt, "
            "incorpora-as; caso contrário, baseia-te apenas na análise atual."
        ),
    )
    price_target: float | None = Field(
        default=None,
        description="Preço-alvo opcional, na moeda de cotação do instrumento.",
    )
    time_horizon: str | None = Field(
        default=None,
        description="Período de detenção recomendado opcional, ex.: '3-6 meses'.",
    )

    @field_validator("price_target", mode="before")
    @classmethod
    def _nullish_float_to_none(cls, v):
        return _coerce_optional_float(v)


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render a PortfolioDecision back to the markdown shape the rest of the system expects.

    Memory log, CLI display, and saved report files all read this markdown,
    so the rendered output preserves the exact section headers (``**Rating**``,
    ``**Executive Summary**``, ``**Investment Thesis**``) that downstream
    parsers and the report writers already handle.
    """
    parts = [
        f"**Classificação**: {decision.rating.value}",
        "",
        f"**Sumário Executivo**: {decision.executive_summary}",
        "",
        f"**Tese de Investimento**: {decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Preço-Alvo**: {decision.price_target}"])
    if decision.time_horizon:
        parts.extend(["", f"**Horizonte Temporal**: {decision.time_horizon}"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Sentiment Analyst
# ---------------------------------------------------------------------------


class SentimentBand(str, Enum):
    """Direção de sentimento discreta produzida pelo Analista de Sentimento.

    Seis níveis mantêm o sinal granular o suficiente para ser acionável, permanecendo
    suficientemente pequeno para que cada fornecedor mapeie de forma fiável a partir
    da sua saída JSON.
    """

    BULLISH = "Bullish"
    MILDLY_BULLISH = "Mildly Bullish"
    NEUTRAL = "Neutral"
    MIXED = "Mixed"
    MILDLY_BEARISH = "Mildly Bearish"
    BEARISH = "Bearish"


class SentimentReport(BaseModel):
    """Relatório de sentimento estruturado produzido pelo Analista de Sentimento.

    Substitui a anterior saída em prosa livre para que os consumidores a jusante
    (dashboards, registos de auditoria, renderizadores PDF, outros agentes) possam ler
    ``overall_band`` e ``overall_score`` sem manter frágeis fallbacks de regex
    que variam com cada versão do modelo. ``narrative`` preserva a rica
    análise fonte a fonte; ``render_sentiment_report`` antepõe um
    cabeçalho determinístico para que o relatório gravado permaneça legível por humanos.
    """

    overall_band: SentimentBand = Field(
        description=(
            "Direção geral do sentimento. Exatamente uma de: "
            "Bullish / Mildly Bullish / Neutral / Mixed / Mildly Bearish / Bearish. "
            "Usa Mixed quando as fontes apontam em direções claramente diferentes. "
            "Usa Neutral apenas quando todas as fontes estão genuinamente silenciosas ou não comprometidas."
        ),
    )
    overall_score: float = Field(
        ge=0.0,
        le=10.0,
        description=(
            "Intensidade numérica do sentimento numa escala de 0–10. "
            "0 = máximo bearish, 5 = neutro, 10 = máximo bullish. "
            "Guia para consistência com overall_band: "
            "Bullish ~6.5–10, Mildly Bullish ~5.5–6.4, Neutral/Mixed ~4.5–5.5, "
            "Mildly Bearish ~3.5–4.4, Bearish ~0–3.4. "
            "Apenas os limites 0–10 são aplicados."
        ),
    )
    confidence: Literal["low", "medium", "high"] = Field(
        description=(
            "Confiança na avaliação com base na qualidade dos dados e tamanho da amostra. "
            "Usa 'low' quando uma ou mais fontes devolveram um placeholder ou menos "
            "de 5 pontos de dados; 'medium' quando os dados estão presentes mas são escassos; "
            "'high' quando as três fontes devolveram dados substanciais."
        ),
    )
    narrative: str = Field(
        description=(
            "Relatório de sentimento completo cobrindo, por ordem: "
            "(1) análise fonte a fonte com evidências específicas (citar contagens "
            "de mensagens, rácios, publicações notáveis); "
            "(2) divergências e alinhamentos entre fontes; "
            "(3) temas narrativos dominantes; "
            "(4) catalisadores e riscos revelados pelos dados; "
            "(5) uma tabela markdown resumindo os principais sinais de sentimento, "
            "a sua direção, fonte e evidência de suporte. "
            "Mantém-no informativo e substantivo: desenvolve cada secção minuciosamente "
            "com evidências concretas para que cada ponto acrescente novo sinal para o trader."
        ),
    )


def render_sentiment_report(report: SentimentReport) -> str:
    """Render a SentimentReport to the markdown shape the rest of the system expects.

    The structured header (band + score + confidence) is prepended to the
    narrative so the saved report is both human-readable and machine-parseable
    without regex.
    """
    return "\n".join([
        f"**Sentimento Geral:** **{report.overall_band.value}** "
        f"(Pontuação: {report.overall_score:.1f}/10)",
        f"**Confiança:** {report.confidence.capitalize()}",
        "",
        report.narrative,
    ])
