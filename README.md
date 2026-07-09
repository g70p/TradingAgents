<!-- ──────────────────────────────────────────────────────────────────────────
     TRADINGAGENTS PT-PT · Fork por G70P
     ────────────────────────────────────────────────────────────────────────── -->

```
 ████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗  █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗
 ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝
    ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ███████╗
    ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════██║
    ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████║
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝

                                  ██████╗ ████████╗       ██████╗ ████████╗
                                  ██╔══██╗╚══██╔══╝       ██╔══██╗╚══██╔══╝
                                  ██████╔╝   ██║   █████╗ ██████╔╝   ██║
                                  ██╔═══╝    ██║   ╚════╝ ██╔═══╝    ██║
                                  ██║        ██║          ██║        ██║
                                  ╚═╝        ╚═╝          ╚═╝        ╚═╝

     Framework Multi-Agente LLM para Trading Financeiro · Português Europeu
```

---

## 🧬 Sobre Este Fork

Este é um fork **substancialmente modificado** do [TradingAgents](https://github.com/TauricResearch/TradingAgents) 
original por Tauric Research. Não é uma simples tradução — é uma reimplementação com metodologia, 
fontes de dados e arquitectura de agentes diferentes.

| Característica | Original (Tauric) | Este Fork (G70P) |
|---|---|---|
| **Idioma** | Inglês | **Português Europeu** |
| **Modelo de Pensamento** | Quick + Deep Thinking | **Deep Thinking em TODOS os agentes** |
| **Rondas de Debate** | 1 | **3 rondas (Bull ↔ Bear)** |
| **Fontes de Dados** | Yahoo Finance, StockTwits, Reddit, FRED | **Yahoo Finance, Google News, Euronext, Jornal de Negócios, Investing.com, CNBC, MarketWatch, ECB, Polymarket** |
| **Dimensionamento** | Manual | **ATR + Kelly Criterion** |
| **Cripto** | Básico | **Multi-exchange (Binance→Bybit→OKX) + CoinGecko + mempool.space** |
| **Sessões de Mercado** | Não | **Fiscal de Horários (Euronext, NYSE, Crypto 24/7)** |
| **Modelo de Relatórios** | Livre | **Estruturado AVA (Visão Geral, Mapa Mental, Quadros, Gates)** |

---

## ⚠️ Avisos Legais

**Este software é experimental e para fins educativos.**

- ❌ **Não é aconselhamento financeiro.** Nenhum agente LLM substitui um consultor financeiro certificado.
- ❌ **Não garante rentabilidade.** O desempenho passado não é indicativo de resultados futuros.
- ⚠️ **Contém bugs.** Este é um trabalho em progresso contínuo. Assume-se que podes perder dinheiro.
- ⚠️ **APIs de terceiros.** Este software depende de Yahoo Finance, Google News, ECB, DeepSeek e outros. A disponibilidade não é garantida.
- 🔒 **Não partilhes chaves API.** As tuas chaves (.env) nunca devem ser commitadas.

**Ao usar este software, assumes todos os riscos. Os autores não se responsabilizam por perdas financeiras.**

---

## 🚀 Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/G70P/TradingAgents.git
cd TradingAgents

# 2. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar
pip install -e .

# 4. Configurar chaves API
cp .env.example .env
# Edita .env com a tua DEEPSEEK_API_KEY
```

**.env mínimo:**
```env
DEEPSEEK_API_KEY=sk-...
TRADINGAGENTS_LLM_PROVIDER=deepseek
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-pro
TRADINGAGENTS_OUTPUT_LANGUAGE=Português
```

---

## 🖥️ Uso

### Menu Interativo
```bash
source .venv/bin/activate
tradingagents
```

```
┌─────────────────────────────────────────┐
│        Bem-vindo ao TradingAgents        │
│         Menu Principal                   │
├─────────────────────────────────────────┤
│  1. Analisar Ticker     (passo a passo)  │
│  2. Análise Rápida      (.env)           │
│  3. Histórico           (análises)        │
│  4. Configuração        (.env actual)     │
│  5. Sair                                 │
└─────────────────────────────────────────┘
```

### Linha de Comandos
```bash
# Análise rápida (usa .env)
tradingagents analyze --quick BCP.LS

# Análise programática
python3 -c "
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

g = TradingAgentsGraph(['market','social','news','fundamentals'],
                        config=DEFAULT_CONFIG.copy(), debug=True)
state, decision = g.propagate('BCP.LS', '2026-07-09', asset_type='stock')
print(decision)
"
```

---

## 📊 Tickers Suportados

### Ações Portuguesas (Euronext Lisbon)
| Ticker | Empresa |
|---|---|
| `BCP.LS` | Banco Comercial Português |
| `EGL.LS` | Mota-Engil |
| `TDSA.LS` | Teixeira Duarte |
| `PHR.LS` | Pharol |
| `EDP.LS` | EDP Energias de Portugal |

### Criptomoedas
| Ticker | Ativo |
|---|---|
| `BTC-USD` | Bitcoin (com dados on-chain) |
| `ETH-USD` | Ethereum |

### Ações Estrangeiras
| Ticker | Empresa |
|---|---|
| `NVDA` | NVIDIA |
| `AAPL` | Apple |
| `GC=F` | Ouro (Commodity) |

---

## 🧠 Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                      TRADINGAGENTS PT-PT                          │
│                                                                   │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────┐ │
│   │  Analista    │   │  Analista    │   │  Analista    │   │ Anal │ │
│   │  Mercado     │   │  Sentimento  │   │  Notícias    │   │ Fund │ │
│   │  (Técnico)   │   │  (Social)    │   │  (Macro)     │   │ (Val)│ │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──┬───┘ │
│          └──────────────────┼──────────────────┼──────────────┘      │
│                             ▼                                       │
│                   ┌─────────────────┐                               │
│                   │  Consolidor AVA  │  ← Relatório unificado        │
│                   └────────┬────────┘                               │
│                            ▼                                        │
│              ┌─────────────────────────┐                            │
│              │   Debate Bull vs Bear    │  ← 3 rondas                │
│              │   🐂 ↔ 🐻               │                            │
│              └────────────┬────────────┘                            │
│                           ▼                                         │
│                   ┌──────────────┐                                  │
│                   │    Trader     │  ← ATR + decisão final           │
│                   └──────┬───────┘                                  │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │   Gestão de Risco      │  ← 3 perfis de risco        │
│              │   Agro • Neutro • Cons │                              │
│              └───────────┬───────────┘                              │
│                          ▼                                          │
│               ┌─────────────────────┐                               │
│               │  Gestor Portfólio    │  ← Decisão final consolidada  │
│               └─────────────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Desenvolvimento

```bash
# Ambiente
source .venv/bin/activate
pip install -e .
find . -name '__pycache__' -exec rm -rf {} +   # limpar cache se necessário
```

---

## 📄 Licença

Baseado em [TradingAgents](https://github.com/TauricResearch/TradingAgents) por Tauric Research.

Este fork: [github.com/G70P/TradingAgents](https://github.com/G70P/TradingAgents)

---

*"Confia, mas verifica." — em trading e em código.*
