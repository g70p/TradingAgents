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
| **Rondas de Debate** | 1 | **2 rondas (Bull ↔ Bear) + 2 rondas de risco** |
| **Analistas** | 4 (Market, Social, News, Fundamentals) | **5 (Market, Social, News, Fundamentals, Math)** |
| **Fontes de Dados** | Yahoo Finance, StockTwits, Reddit, FRED | **Yahoo Finance, ECB, Polymarket + RSS PT (ECO, J. Negócios, RTP)** |
| **Ferramentas Quant** | Não | **HMM (Baum), Bachelier, Mandelbrot, Kelly (Thorp), Black-Scholes-Merton** |
| **Volume Framework** | Não | **Leitura tática G70P — campo de batalha, engodo, P&L** |
| **Modo Dados Crus** | Não | **collect_data() — zero tokens, zero LLM** |
| **Dimensionamento** | Manual | **ATR + Kelly Criterion** |
| **Sessões de Mercado** | Não | **Fiscal de Horários (Euronext, NYSE, Crypto 24/7)** |
| **Modelo de Relatórios** | Livre | **AVA (Análise → Validação → Ação) em todos os agentes** |
| **Output Telegram** | Não | **Professor 👨‍🏫 — explicação simples, formato AVA, zero jargão** |

---

## 🧠 Arquitectura

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      TRADINGAGENTS PT-PT — g70p                           │
│                                                                           │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐          │
│   │ Market  │→│ Social  │→│  News   │→│Fundament. │→│  MATH   │          │
│   │(Técnico)│ │(Sentim.)│ │ (Macro) │ │(Balanços)│ │(HMM-Kelly)│          │
│   └─────────┘ └─────────┘ └─────────┘ └──────────┘ └────┬────┘          │
│                                                          ▼                │
│                                ┌─────────────────────┐                   │
│                                │ Debate Bull vs Bear  │ ← 2 rondas        │
│                                │ 🐂 ↔ 🐻             │                   │
│                                └──────────┬──────────┘                   │
│                                           ▼                               │
│                                    ┌────────────┐                        │
│                                    │   Trader    │ ← ATR + Kelly          │
│                                    └─────┬──────┘                        │
│                                          ▼                                │
│                               ┌───────────────────┐                      │
│                               │  Gestão de Risco   │ ← 3 perfis          │
│                               │ Agro · Neutro · Cons│   2 rondas          │
│                               └─────────┬─────────┘                      │
│                                         ▼                                 │
│                              ┌─────────────────────┐                     │
│                              │  Gestor Portfólio    │ ← Decisão final     │
│                              └──────────┬──────────┘                     │
│                                         ▼                                 │
│                              ┌─────────────────────┐                     │
│                              │     Professor 👨‍🏫    │ ← Explicação        │
│                              │  (para Telegram)    │    simples PT        │
│                              └─────────────────────┘                     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Math Analyst (novo)

Ferramentas determinísticas — zero risco de alucinação nos números:

| Ferramenta | Autor | Função |
|---|---|---|
| `get_regime_detection` | Baum (1960s) | Hidden Markov Model — regime bull/bear/sideways |
| `get_expected_price_range` | Bachelier (1900) | Cone de preço browniano — intervalo esperado |
| `get_tail_risk` | Mandelbrot (1963) | Expoente α da cauda — risco de outlier estrutural |
| `get_kelly_sizing` | Thorp (1960s) | Kelly Criterion — fração ótima de capital |
| `get_implied_volatility` | Black-Scholes-Merton (1973) | Vol implícita + Gregos |

### Volume Framework

Injetado nos prompts de 6 agentes (Market, Bull, Bear, Research Manager, Professor, Math).
Princípios de leitura tática do G70P — volume como campo de batalha, sem pausas, engodo como arma do vencedor.

---

## 🚀 Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/G70P/TradingAgents.git
cd TradingAgents

# 2. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar (com dependências do Math Agent)
pip install -e .
pip install hmmlearn scipy

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

### Linha de Comandos
```bash
# Análise rápida (usa .env)
tradingagents analyze --quick BCP.LS

# Análise programática com Math Agent
python3 -c "
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

g = TradingAgentsGraph(['market','social','news','fundamentals','math'],
                        config=DEFAULT_CONFIG.copy(), debug=True)
state, decision = g.propagate('BCP.LS', '2026-07-16', asset_type='stock')
print(decision)
"
```

### Modo Dados Crus (zero tokens)
```python
# Recolhe dados sem correr o LLM — para boletins, pré-visualização, debugging
data = g.collect_data('BTC-USD', '2026-07-16', asset_type='crypto')
print(data['ticker_news'])      # Notícias do ticker
print(data['global_news'])      # Notícias globais + RSS português
print(data['market_snapshot'])  # OHLCV
```

---

## 📊 Tickers e Fontes

### Ações PSI-20 (Euronext Lisbon)
BCP.LS, EGL.LS, TDSA.LS, PHR.LS, EDP.LS, EDPR.LS, GALP.LS, JMT.LS, NOS.LS, RENE.LS, SEM.LS, SON.LS, CTT.LS, ALTR.LS, COR.LS, IBS.LS, SNG.LS, RAM.LS, VAF.LS, NVG.LS, NBA.LS

### Criptomoedas
BTC-USD (com dados on-chain: funding rate, open interest)

### Fontes de Notícias
- Yahoo Finance (global)
- RSS Português: **ECO** (economia), **Jornal de Negócios** (mercados), **RTP** (nacional)

---

## ⚠️ Avisos Legais

**LEIA ATENTAMENTE ANTES DE USAR ESTE SOFTWARE.**

Este software é disponibilizado **exclusivamente para fins educativos, de investigação e estudo**.
Nada neste software constitui aconselhamento financeiro. Os outputs dos agentes LLM são
simulações automáticas — nunca tomes decisões financeiras baseadas exclusivamente em outputs de IA.

**AO USAR ESTE SOFTWARE, RECONHECES QUE LESTE, COMPREENDESTE E ACEITAS ESTES TERMOS.**

---

## 📄 Licença

Baseado em [TradingAgents](https://github.com/TauricResearch/TradingAgents) por Tauric Research.

Este fork: [github.com/G70P/TradingAgents](https://github.com/G70P/TradingAgents)

---

*"Confia, mas verifica." — em trading e em código.*
