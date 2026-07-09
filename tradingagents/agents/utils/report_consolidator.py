"""Consolidador de Relatórios — unifica os outputs dos 4 analistas num documento AVA.

Antes de alimentar o debate Bull vs Bear, os relatórios de Mercado, Sentimento,
Notícias e Fundamentais são fundidos numa estrutura padronizada com:
  1. Visão Geral
  2. Mapa Mental
  3. Quadro de Sinais Consolidado
  4. Detalhe por Fonte
  5. Riscos e Catalisadores Agregados
  6. Gate de Validação
"""


def consolidate_analyst_reports(
    market_report: str,
    sentiment_report: str,
    news_report: str,
    fundamentals_report: str,
    ticker: str,
    trade_date: str,
) -> str:
    """Merge four analyst reports into a single AVA-structured document.

    Each report is included as a section under the unified structure.
    Reports that are empty or unavailable are gracefully omitted.
    """
    sections = []

    # ── Header ───────────────────────────────────────────────────────
    sections.append(f"# Relatório Consolidado de Análise — {ticker} | {trade_date}")
    sections.append("")

    # ── 1. Visão Geral ───────────────────────────────────────────────
    sections.append("## 1. Visão Geral")
    sections.append("")
    sections.append(
        f"Documento unificado que agrega as análises independentes de 4 especialistas "
        f"(Técnico, Sentimento, Notícias/Macro, Fundamental) sobre **{ticker}** "
        f"na data de **{trade_date}**. Cada analista trabalhou isoladamente com "
        f"as suas ferramentas especializadas. Este documento serve como base para "
        f"o debate Bull vs Bear e a decisão final de trading."
    )
    sections.append("")

    # ── 2. Mapa Mental ───────────────────────────────────────────────
    sections.append("## 2. Mapa Mental da Análise")
    sections.append("")
    sections.append("```")
    sections.append(f"Análise Consolidada — {ticker}")
    sections.append("├── Análise Técnica (Mercado)")
    sections.append("│   ├── Tendência (MAs, MACD)")
    sections.append("│   ├── Momentum (RSI)")
    sections.append("│   └── Volatilidade (Bollinger, ATR)")
    sections.append("├── Análise de Sentimento")
    sections.append("│   ├── Fontes Institucionais (Yahoo Finance)")
    sections.append("│   ├── Fontes Mediáticas (Google News)")
    sections.append("│   └── Fontes Agregadas (Euronext, Investing, CNBC)")
    sections.append("├── Análise de Notícias e Macro")
    sections.append("│   ├── Notícias Específicas (7 dias)")
    sections.append("│   ├── Notícias Globais")
    sections.append("│   ├── Indicadores Macro (BCE)")
    sections.append("│   └── Mercados de Previsão (Polymarket)")
    sections.append("├── Análise Fundamental")
    sections.append("│   ├── Capitalização de Mercado")
    sections.append("│   ├── Rácios Financeiros")
    sections.append("│   └── Posicionamento na Faixa de 52 Semanas")
    sections.append("├── Debate Bull vs Bear (a seguir)")
    sections.append("└── Decisão Final de Trading")
    sections.append("```")
    sections.append("")

    # ── 3-6. Relatórios individuais ──────────────────────────────────
    reports = [
        ("3. Análise Técnica (Analista de Mercado)", market_report),
        ("4. Análise de Sentimento (Analista de Sentimento)", sentiment_report),
        ("5. Análise de Notícias e Macro (Analista de Notícias)", news_report),
        ("6. Análise Fundamental (Analista de Fundamentais)", fundamentals_report),
    ]

    for title, content in reports:
        if content and content.strip() and "indisponível" not in content[:50].lower():
            sections.append(f"## {title}")
            sections.append("")
            sections.append(content.strip())
            sections.append("")

    # ── 7. Gate de Validação da Consolidação ─────────────────────────
    sections.append("## 7. Gate de Validação")
    sections.append("")
    sections.append("Antes de avançar para o debate Bull vs Bear, verifica:")
    for r in reports:
        status = "✅" if r[1] and r[1].strip() else "⚠️"
        sections.append(f"- [{status}] {r[0]} — {'presente' if r[1] and r[1].strip() else 'ausente ou indisponível'}")
    sections.append("")

    return "\n".join(sections)
