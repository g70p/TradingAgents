#!/bin/bash
# Exemplo: como correr o TradingAgents para um ticker.
# Os 4 scripts reais em ~/.hermes/scripts/ são variantes disto.
set -e

# 1. Activar o ambiente virtual e carregar chaves API
cd "$(dirname "$0")/.."
source .venv/bin/activate
set -a && source .env && set +a

# 2. Escolher ticker e data
TICKER="${1:-BTC-USD}"
DATE="${2:-$(date +%Y-%m-%d)}"

# 3. Correr a análise (detecta asset_type automaticamente)
python3 -c "
import sys; sys.path.insert(0, '.')
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

asset_type = 'crypto' if '$TICKER'.endswith('-USD') else 'stock'
config = DEFAULT_CONFIG.copy()

print(f'🔍 A analisar $TICKER ({asset_type}) — $DATE')
ta = TradingAgentsGraph(debug=False, config=config)
_, decision = ta.propagate('$TICKER', '$DATE', asset_type=asset_type)

# Guardar relatórios
report_path = ta.save_reports(ta.curr_state, '$TICKER')
print(f'📁 Relatórios: {report_path}')
print()
print(decision)
"
