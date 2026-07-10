# Development Notes — G70P Fork

> Última atualização: 2026-07-10

---

## 1. Modelo Flash vs Pro

**Decisão**: Ambos os LLMs `deepseek-v4-flash`. Zero v4-pro.

**Justificação**: O v4-pro é desnecessário para profundidade quando a direção já está clara. Os agentes seguem prompts bem estruturados — o modelo certo não é o mais "inteligente", é o mais rápido e barato que cumpre.

**Risco conhecido**: O v4-flash falha ocasionalmente no *structured output* (Pydantic schema). Exemplo: Portfolio Manager em EGL.LS devolveu `structured output returned no parsed result`, caiu para free text, e a decisão final foi `Hold` (possível default de fallback).

**Não alterar modelos**. Se houver falhas de parsing, resolver no código (retry, fallback mais robusto), não trocar de modelo.

---

## 2. Volume em Tempo Real — FALTA

**Problema**: Nenhum analista está a pedir dados de volume concreto. Volume é a quantidade de shares a passar de mãos no momento exato — essencial para confirmar breakouts, detectar distribuição, validar suporte/resistência.

**O que é preciso**:
- Volume intraday (não só o OHLCV diário que o yfinance dá)
- Volume profile / zonas de alto volume
- Delta volume (compras vs vendas)

**Fontes possíveis**: Yahoo Finance tem volume diário mas não intraday. Para Euronext Lisbon, dados em tempo real são pagos. Alternativas: Google Finance scraping, ou aceitar volume diário com mais granularidade.

---

## 3. Pré-Researcher + Fiscal de Horários

### Conceito
Antes de cada sessão de mercado, um agente leve (pré-researcher) prepara contexto que alimenta os analistas principais.

### Fiscal de Horários
Cron job que conhece os horários de cada bolsa e dispara o pipeline no momento certo:

| Mercado | Sessão | Hora PT | Pré-Researcher | Análise Completa |
|---|---|---|---|---|
| Euronext Lisbon | 08:00-16:30 | 07:00 | 06:55 | 07:00 |
| Crypto | 24/7 | 07:30, 13:30, 18:30 | 5 min antes | à hora |

### Pré-Researcher (1 agente, v4-flash)
Input: ticker + data
Output: relatório de contexto de sessão

Foco:
- Volume anormal vs média 20 dias
- VWAP do dia anterior
- Gap vs fecho anterior
- Volatilidade (ATR, Bollinger width)
- Níveis de suporte/resistência para a sessão
- Eventos no calendário (resultados, dividendos, macro)

Este relatório é injectado como contexto adicional no Market Analyst.

### Arquitectura proposta
```
Fiscal de Horários (cron)
  │
  ├─ [pré-researcher] 1 agente, 1 ticker (~30s com flash)
  │     └─ output → ficheiro ou env var
  │
  └─ [TradingAgents] 11 agentes, 1 ticker (~6 min com flash)
        └─ Market Analyst recebe output do pré-researcher como contexto extra
```

---

## 4. Structured Output Failures

**EGL.LS (2026-07-10)**: `Portfolio Manager: structured-output invocation failed (structured output returned no parsed result); retrying once as free text`

**Causa provável**: v4-flash não suporta tão bem Pydantic/JSON schema como v4-pro. O fallback para free text funciona, mas a decisão pode ser menos precisa.

**A investigar**:
- Adicionar retry com temperatura ligeiramente diferente
- Validar o output do free text contra o schema esperado
- Logging de quando o fallback é activado vs sucesso

---

## 5. Pendentes

- [ ] Fiscal de Horários — cron job que conhece calendários de bolsas
- [ ] Pré-Researcher — agente único de contexto de sessão
- [ ] Volume intraday — encontrar fonte gratuita para Euronext
- [ ] Structured output — melhorar fallback quando flash falha parsing
- [ ] Professor — não está a gravar `professor_message` no state (BCP.LS veio vazio)
