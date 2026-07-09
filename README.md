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

## ⚠️ Avisos Legais e Isenção de Responsabilidade

**LEIA ATENTAMENTE ANTES DE USAR ESTE SOFTWARE.**

### 1. Não é Aconselhamento Financeiro

Este software é disponibilizado **exclusivamente para fins educativos, de investigação e estudo**. 
Nada neste software constitui aconselhamento financeiro, recomendação de investimento, 
solicitação ou oferta de compra ou venda de quaisquer instrumentos financeiros.

As análises, relatórios e decisões geradas pelos agentes LLM são **simulações automáticas** 
produzidas por modelos de inteligência artificial. Não refletem a opinião de analistas 
financeiros certificados, consultores de investimento ou quaisquer profissionais 
credenciados junto da CMVM, SEC, FCA ou qualquer outro regulador.

**Nunca tomes decisões financeiras baseadas exclusivamente em outputs de IA.**

### 2. Risco de Perda Financeira Significativa

Investir e negociar nos mercados financeiros envolve **risco substancial de perda**.
Podes perder **todo o capital investido** e potencialmente mais do que investiste
(no caso de produtos alavancados, futuros, opções ou CFDs).

- ❌ **Não invistas dinheiro que não possas perder.**
- ❌ **Não uses dinheiro destinado a necessidades básicas, saúde, educação ou reforma.**
- ❌ **Não invistas com base em empréstimos ou crédito.**
- ❌ **O desempenho passado não garante resultados futuros.**

### 3. Resultados Não Garantidos

Os resultados produzidos por este framework podem variar significativamente em função de:

- O modelo LLM utilizado (DeepSeek, OpenAI, Anthropic, etc.)
- A configuração do sistema (temperatura, número de rondas, agentes selecionados)
- O período temporal analisado
- A qualidade e disponibilidade das fontes de dados externas
- A máquina onde o software é executado (diferentes ambientes podem produzir resultados diferentes)
- Alterações nas APIs de terceiros (Yahoo Finance, Google News, ECB, etc.)

**Nenhum teste, backtest ou simulação pode garantir rentabilidade futura.** 
Os mercados são influenciados por fatores imprevisíveis que nenhum modelo de IA 
pode antecipar completamente.

### 4. Dados de Terceiros

Este software depende de APIs e fontes de dados externas que podem:

- Estar indisponíveis ou sofrer interrupções
- Conter erros, omissões ou atrasos
- Alterar formatos ou termos de serviço sem aviso prévio
- Fornecer dados desatualizados ou incompletos

Os autores não garantem a exatidão, integridade ou atualidade de quaisquer dados 
obtidos através deste software.

### 5. Responsabilidade do Utilizador

Ao utilizar este software, **assumes integralmente todos os riscos** associados às 
tuas decisões de investimento. Os autores, contribuidores e afiliados **não se 
responsabilizam por**:

- Perdas financeiras diretas ou indiretas
- Danos consequentes ou incidentais
- Lucros cessantes
- Decisões de trading baseadas nos outputs do software
- Erros, bugs ou comportamentos inesperados do software
- Alterações nos mercados que invalidem análises anteriores

### 6. Conformidade Regulatória

Este software não está registado, licenciado ou aprovado por qualquer autoridade 
reguladora financeira, incluindo mas não limitado a:

- CMVM (Comissão do Mercado de Valores Mobiliários) — Portugal
- SEC (Securities and Exchange Commission) — EUA
- FCA (Financial Conduct Authority) — Reino Unido
- ESMA (European Securities and Markets Authority) — UE

### 7. Sem Garantia

Este software é fornecido **"AS IS"** (tal como está), sem garantias de qualquer tipo, 
expressas ou implícitas, incluindo mas não limitado a garantias de comercialização, 
adequação a um fim específico ou não violação.

---

**AO USAR ESTE SOFTWARE, RECONHECES QUE LESTE, COMPREENDESTE E ACEITAS ESTES TERMOS 
NA SUA TOTALIDADE. SE NÃO CONCORDAS, NÃO UTILIZES O SOFTWARE.**

---

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
