# Validação da ronda de correções — 16/17-09-2026

## Resultado e âmbito

O percurso principal é recolha/cálculo local seguido de análise na sessão Codex,
sem chaves ou SDKs de modelos na instalação normal. Fontes públicas continuam
online. O backend API é compatibilidade opcional e não foi usado no ensaio real.

Não se confunde validação de software com rentabilidade, recomendação aprovada
ou revisão humana. A análise real terminou em REVIEW e está disponível para revisão.

## Verificações executadas

- Python 3.12.14 no Windows; ambiente isolado e instalação limpa separados.
- Suite completa: 698 testes aprovados, 2 ignorados e 69 subtestes aprovados.
- Os ignorados são Bedrock sem SDK opcional e chamada real DeepSeek sem chave.
- Ruff e verificação de whitespace/diff aprovados.
- Instalação normal: importação e CLI sem `openai`, `anthropic`, `langchain_core`
  ou `langgraph`. `scripts/smoke_local.py` gera e valida dossiers sintéticos de
  EDP.LS, MSFT e BTC-USD com rede bloqueada.
- Grafo de compatibilidade completo com modelo simulado, com e sem Math,
  incluindo debate, gestores, Trader, Professor e escrita de relatórios.
- Testes de checkpoints cobrem interrupção/retoma; o percurso local preserva
  a evidência e pode retomar a escrita antes da finalização.
- Testes de finalização rejeitam preços alterados, caminhos fora do conjunto
  esperado, divergência do Professor e substituição indevida de REVIEW.

## Evidência das correções

| Área | Correção/decisão | Evidência |
|---|---|---|
| Datas e fontes | Janelas UTC, RSS datado, cache OHLCV e bloqueio de dados atuais em recolha histórica | Testes de notícias, RSS, cache, fundamentais e `test_completion_regressions.py` |
| Memória/checkpoints | Corte temporal, janela completa e retoma sem duplicação | `test_memory_pointintime.py`, `test_checkpoint_lifecycle.py` |
| ATR | Quantidade versus valor monetário, teto de exposição, stop por direção e inputs válidos | `test_fork_sizing_and_decisions.py` |
| Math | Nó/estado/relatórios ligados; quantil analítico, HMM com convergência e rótulos por estatística | `test_local_codex.py`, `test_completion_regressions.py` |
| Kelly/caudas/opções | Uma implementação de Kelly, Half-Kelly antes do teto, Hill sem equivalência a lei estável e IV com limites | `test_completion_regressions.py` |
| Decisão/Professor | AVA narrativo separado do rating; números e classificação verificados | `test_fork_sizing_and_decisions.py`, `test_completion_regressions.py` |
| Sessões | Horários indicativos, calendário não verificado explícito; data histórica sem hora não usa estado atual | `test_completion_regressions.py` |
| Reddit legado | U14 aplicado: leitura limitada, backoff e indisponibilidade explícita | `test_reddit_fallback.py` |
| Conclusão Codex | Hashes, campos, estrutura AVA e classificação concordante | `test_dossier_review.py` |

## Ensaio com dados reais

Dossier local: `reports/validacao-real-final/MSFT_2026-09-15_20260916T225548621721Z/`.
É ignorado pelo Git, tal como os restantes relatórios de execução.

- Ativo MSFT, data limite 15-09-2026, fim do dia UTC.
- 1254 barras recolhidas, última barra na data solicitada; RSS com datas e URLs.
- Recolha final registada às 22:55:48 UTC de 16-09-2026, análise/finalização nessa sessão.
- Divulgação oficial Microsoft anterior ao corte consultada pelo Codex e ligada
  em `fontes_adicionais.md`; detalhes quantitativos em ficheiros próprios.
- Relatório com analistas, duas rondas Bull/Bear, Trader, duas rondas de risco,
  gestor e Professor. Decisão: REVIEW, sem quantidade de posição nem ordens.
- `validacao.json` regista conclusão técnica e **revisão humana pendente**.
- Não houve chamadas a APIs de modelos feitas pelo projeto. A análise usa o
  serviço Codex autenticado. Tokens/custo exclusivos deste ensaio não foram
  medidos; não devem ser descritos como zero.

## Limites da entrega

- Sem comprovação de rentabilidade ou backtest point-in-time. Preços ajustados
  recolhidos hoje podem ter revisões; notícias de fim do dia UTC podem ser posteriores
  ao fecho americano. Os cenários do relatório são ilustrativos, não ordens.
- Calendários oficiais/feriados não foram implementados: o sistema não afirma
  que a bolsa está aberta com base apenas no horário semanal.
- Fundamentais completos, macro vintage, opções e on-chain não são recolhidos
  automaticamente pelo novo comando. Ausência fica explícita; pode ser complementada
  na sessão Codex com fontes datadas, como ocorreu com a divulgação oficial.
- Os testes API são simulados. Não foram feitas chamadas pagas de validação nem
  ensaios reais dos fornecedores opcionais.
- A versão 0.4.0 foi publicada na branch `g70p` em 17-09-2026
  através da integração GitHub.
  O README publicado foi comparado com a cópia local. Uma instalação limpa da
  versão 0.4.0 passou os comandos de ajuda e o smoke test sem SDKs de modelos.
- CI foi configurado, mas ainda não há execuções no GitHub. A consulta pública
  mostra zero workflows/runs; sem sessão administrativa no navegador, não foi
  possível confirmar se Actions está desativado no fork. A validação remota
  permanece pendente e não deve ser confundida com os testes locais aprovados.
