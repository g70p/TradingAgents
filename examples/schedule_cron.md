# Agendamento com Cron (Linux/macOS)

Este guia mostra como agendar análises automáticas do TradingAgents.

## Pré-requisitos

- Python 3.12+ com virtualenv em `.venv`
- Ficheiro `.env` com as chaves API (ex: `DEEPSEEK_API_KEY`)
- TradingAgents instalado (`pip install -e .` ou no PATH)

## Exemplo básico

O script `examples/run_analysis.sh` aceita ticker e data:

```bash
# Análise única
bash examples/run_analysis.sh BCP.LS 2026-07-09
bash examples/run_analysis.sh BTC-USD
```

## Carteira múltipla

Cria um script para a tua carteira:

```bash
#!/bin/bash
# ~/scripts/minha_carteira.sh
cd ~/projects/TradingAgents
source .venv/bin/activate
set -a && source .env && set +a

TICKERS=("BCP.LS" "EDP.LS" "BTC-USD")
DATE=$(date +%Y-%m-%d)

for ticker in "${TICKERS[@]}"; do
    python3 -c "
import sys; sys.path.insert(0, '.')
from tradingagents.graph.trading_graph import TradingAgentsGraph

asset_type = 'crypto' if '$ticker'.endswith('-USD') else 'stock'
ta = TradingAgentsGraph(debug=False)
_, decision = ta.propagate('$ticker', '$DATE', asset_type=asset_type)
ta.save_reports(ta.curr_state, '$ticker')
print(decision)
"
done
```

## Agendar com cron

```bash
# Editar o crontab
crontab -e

# Exemplos:
# Ações europeias: 7:00, 13:00, 17:30 dias úteis
0 7,13 * * 1-5 bash ~/scripts/minha_carteira.sh
30 17 * * 1-5 bash ~/scripts/minha_carteira.sh

# Cripto: todos os dias (mercado 24/7)
0 7,13,19 * * * bash ~/scripts/crypto_carteira.sh
```

## Integração com Telegram

Para receber as análises no Telegram, redireciona o output:

```bash
30 17 * * 1-5 bash ~/scripts/carteira.sh | curl -s -X POST \
  -d "chat_id=TEU_CHAT_ID&text=$(cat)" \
  "https://api.telegram.org/botTEU_BOT_TOKEN/sendMessage"
```

## Horários das Sessões de Mercado

O Fiscal de Sessões (`market_sessions.py`) injeta automaticamente o estado:

| Bolsa | Horário (local) | Fuso |
|---|---|---|
| Euronext Lisbon | 08:00–16:30 | CET/CEST |
| NYSE/NASDAQ | 09:30–16:00 | EST/EDT |
| Cripto | 24/7 | UTC |

O framework sabe se o mercado está aberto, fechado, em pré-mercado ou pós-fecho e ajusta as recomendações.
