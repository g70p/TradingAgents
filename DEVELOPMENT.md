# DEVELOPMENT.md — TradingAgents Fork G70P

Notas de desenvolvimento, correções e decisões de design.

## 2026-07-10: Professor Agent NÃO integrado no grafo (BUG CRÍTICO)

**Sintoma:** `professor_message` sempre vazio. Scripts cron mostravam só "BCP.LS: Buy" sem análise.

**Causa:** O `professor_node` era criado em `setup.py:103` mas NUNCA adicionado ao grafo.
- Faltava `workflow.add_node("Professor", professor_node)`
- O edge era `Portfolio Manager → END` (linha 166), devia ser `PM → Professor → END`

**Fix:** Adicionado nó + edges corrigidos. Commit necessário.

## 2026-07-10: Scripts cron com NameError e timeout

**Sintomas:**
- `NameError: name 'ticker' is not defined` no print fallback
- `set -e` matava o loop ao primeiro erro
- Timeout de 30 min insuficiente para 4 tickers

**Fixes:**
- `f'{ticker}: {decision}'` → `f'{t}: {decision}'`
- Removido `set -e`, adicionado `try/except` + `|| echo "❌"`
- `(state or {}).get(...)` seguro contra state=None
- Timeout global: 1800s → 3600s

## 2026-07-10: v4-flash escolhido (velocidade > profundidade)

Ambos LLMs (deep e quick think) usam `deepseek-v4-flash`. ~6 min/ticker vs 27 min com v4-pro.
v4-pro disponível via `.env` se necessário. NUNCA trocar modelo para resolver bugs.

## 2026-07-10: Structured output fallback no Portfolio Manager

v4-flash ocasionalmente falha structured output ("no parsed result"). O `parse_rating` já trata
free-text fallback. Prompt do PM exige `**Rating**: <Comprar|...>` + AVA. Ver `portfolio_manager.py`.

## Regras gerais

- NUNCA `llm.bind(temperature=X)` com DeepSeek — ignora e retorna objeto partido
- Merge upstream: só fixes substanciais (bugs, modelos, providers). Refactors cosméticos mantêm fork
- Prompts sempre PT-PT europeu
- Cron SEQUENCIAL (nunca paralelo — satura API DeepSeek)
- `debug=True` agora é seguro (todos os 3 root causes do 'Bull Researcher' resolvidos)
