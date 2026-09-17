# TradingAgents G70P — análise financeira local com Codex

**Versão 0.4.0 · Português europeu · branch `g70p`**

Fork do [TradingAgents de Tauric Research](https://github.com/TauricResearch/TradingAgents),
adaptado para trabalhar na tua sessão do Codex, **sem configurar chaves API de
modelos de IA**. Recolhe dados públicos, calcula métricas em Python e organiza
uma análise com fontes e limitações explícitas.

O fluxo é: **dados → analistas → debate Bull/Bear → Trader → risco → gestor → Professor**.
Os papéis são executados sequencialmente no Codex. A metodologia AVA significa
**Análise → Validação → Ação**; o Professor explica a conclusão em linguagem simples.
Não existe um botão autónomo de trading e o projeto não envia ordens.

## O que precisas

- **Python 3.12 recomendado**, que foi validado localmente; o projeto declara Python 3.10 ou superior.
- **Git**, para clonar e atualizar o projeto, ou o ZIP da branch indicada abaixo.
- **Codex com acesso à pasta local**, autenticado com a tua conta ChatGPT.
  Consulta o [guia oficial de início](https://learn.chatgpt.com/docs/quickstart)
  e a [autenticação oficial](https://learn.chatgpt.com/docs/auth).
- Internet para instalar dependências, obter preços/notícias e usar o Codex.

Não precisas de criar `.env`, escolher DeepSeek ou instalar SDKs de modelos.
O acesso ao Codex depende do teu plano e limites. “Local” refere-se ao projeto,
à execução Python e aos ficheiros: **o modelo Codex não funciona offline**, e os
dados que lhe pedires para analisar podem ser processados pelo serviço Codex.

## 1. Obter a versão certa

No terminal, numa pasta à tua escolha:

```shell
git clone --branch g70p --single-branch https://github.com/g70p/TradingAgents.git
cd TradingAgents
```

Sem Git: [descarrega o ZIP da branch g70p](https://github.com/g70p/TradingAgents/archive/refs/heads/g70p.zip),
extrai-o e abre o terminal na pasta que contém `main.py` e `pyproject.toml`.
**Usa a branch `g70p`**; a branch `main` do fork não é o guia desta versão.

## 2. Instalar num ambiente isolado

### Windows — PowerShell

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe main.py --help
```

Se `python` não for reconhecido ou abrir a Microsoft Store, instala Python e
reabre o terminal; se tiveres o lançador Windows, podes usar `py -3.12` nos dois
primeiros comandos. Não é necessário ativar o ambiente nem alterar a política
de execução do PowerShell.

### macOS / Linux

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python main.py --help
```

Em sistemas que separam o módulo `venv`, instala o pacote correspondente à tua
versão de Python através do gestor de pacotes do sistema.

## 3. Pedir uma análise no Codex

Abre a pasta do projeto no Codex. Podes pedir-lhe para executar o processo todo:

> Lê o README deste projeto. Usa o Python da .venv para recolher dados de MSFT até ontem, através de main.py. Depois lê ANALISAR_NO_CODEX.md na pasta criada e executa todos os papéis sequencialmente nesta sessão. Guarda relatório, decisão e Professor e executa o validador. Não uses APIs de modelos, não inventes dados em falta e não envies ordens. Mostra-me a pasta dos resultados e as limitações.

Substitui `MSFT` pelo símbolo pretendido. Para Bitcoin, indica `BTC-USD` e pede
`--asset-type crypto`. Podes pedir uma data explícita em formato `YYYY-MM-DD`.

Para iniciar apenas a recolha manualmente, no Windows:

```powershell
.\.venv\Scripts\python.exe main.py MSFT
```

Ou em macOS/Linux:

```bash
.venv/bin/python main.py MSFT
```

Sem `--date`, usa a data atual; a última barra pode estar incompleta. Para estudar
uma sessão fechada, fornece a data correspondente. Exemplos Windows:

```powershell
.\.venv\Scripts\python.exe main.py EDP.LS --date 2026-09-15
.\.venv\Scripts\python.exe main.py BTC-USD --asset-type crypto --date 2026-09-15
```

Estas datas são exemplos: escolhe a data pretendida. No macOS/Linux, troca o
executável pelo da secção anterior. A disponibilidade depende da fonte e do símbolo.

O comando imprime `Dossier: ...` com o caminho completo em `reports/`.
**Esse comando prepara a evidência; ainda não produz a análise do Codex.**
Para continuar uma recolha manual, envia ao Codex:

> Lê ANALISAR_NO_CODEX.md na pasta [cola aqui o caminho do dossier] e executa a análise completa. Segue o roteiro, grava os resultados e executa a validação final.

## 4. Ler e validar os resultados

| Ficheiro | Conteúdo | Quem o produz |
|---|---|---|
| `precos.csv` | Preços/volume validados e cortados pela data | Python |
| `noticias.md` | Manchetes RSS com publicações e ligações, quando disponíveis | Python |
| `quantitativo.json` | Projeção lognormal, caudas e regimes HMM, ou erros explícitos | Python |
| `manifesto.json` | Fonte, datas, limitações e hashes da evidência | Python |
| `ANALISAR_NO_CODEX.md` | Roteiro dos papéis e contratos de saída | Python |
| `relatorio.md` | Análise, debates, cenários e conclusão | Codex |
| `decisao.json` | Classificação, justificação e limitações | Codex |
| `professor.md` | Explicação simples da mesma decisão | Codex |
| `notas_video.md` | Notas para eventual utilização futura em conteúdo educativo | Codex |
| `validacao.json` | Resultado da verificação automática | Validador Python |

As classificações são `Buy`, `Overweight`, `Hold`, `Underweight`, `Sell` e
`REVIEW`. **REVIEW significa que é preciso rever ou completar a evidência**;
não é uma recomendação automática de manter nem um erro a esconder.

O Codex deve executar, no fim (substitui o caminho pelo mostrado na recolha):

```powershell
.\.venv\Scripts\python.exe -m cli.review "reports/PASTA_DO_DOSSIER"
```

```bash
.venv/bin/python -m cli.review "reports/PASTA_DO_DOSSIER"
```

A validação confirma hashes, campos, formato AVA e classificação concordante.
Não certifica a qualidade financeira da conclusão. O estado original da recolha
fica preservado; a conclusão aparece em `validacao.json`, com revisão humana pendente.

Não precisas de enviar o dossier para o GitHub: `reports/` está ignorada pelo Git.
Se pedires dimensionamento, fornece capital, moeda da conta e parâmetros de risco;
sem esses dados não deve ser inventada uma quantidade de posição.

## Retomar, atualizar e usar dados próprios

**Sessão interrompida:** abre o mesmo projeto e pede ao Codex para reler o roteiro
da mesma pasta, verificar os hashes e concluir as etapas em falta. Não substituas
silenciosamente os dados originais por uma nova recolha.

**Atualizar uma instalação clonada**, depois de guardar alterações próprias:

```shell
git pull --ff-only origin g70p
```

Volta a executar o comando de instalação `python -m pip install -e .` usando o
Python da `.venv`, conforme o teu sistema. O `--ff-only` recusa combinar histórias
divergentes automaticamente; resolve alterações locais antes de continuar.

**CSV próprio**, sem recolha de notícias (exemplo Windows):

```powershell
.\.venv\Scripts\python.exe main.py MSFT --date 2026-09-15 --csv "meus_precos.csv" --no-news
```

O CSV deve ter `Date,Open,High,Low,Close,Volume`, datas legíveis como `YYYY-MM-DD`
e números com ponto decimal. Preços devem ser positivos, volume não negativo,
e máximos/mínimos coerentes. Esta combinação prepara o dossier sem rede; a análise
Codex continua a depender do serviço. `--output` permite escolher outra pasta de resultados.

## Problemas frequentes

| Situação | O que fazer |
|---|---|
| `ModuleNotFoundError` | Usa o Python da `.venv` e reinstala com `-m pip install -e .`. |
| O programa pede uma chave API ou abre o menu antigo | Confirma a branch `g70p`, atualiza a instalação e executa `main.py`; `python -m cli.main` é o backend antigo. |
| Fonte indisponível / limite de pedidos / sem preços | Confirma o símbolo e a data, tenta mais tarde ou usa CSV próprio. Não substituas a falha por preços inventados. |
| Não há `relatorio.md` | Só a recolha terminou; pede ao Codex para executar o roteiro da pasta. |
| Hash alterado ou classificação incoerente | Pede ao Codex para explicar e corrigir a inconsistência; não alteres os hashes apenas para passar a validação. |
| Falta `decisao.json` ou `professor.md` | Retoma o roteiro na mesma pasta e conclui os ficheiros antes de validar. |

## Cobertura e limites

O coletor atual usa Yahoo Finance e Google News RSS, sem chaves de dados pagas.
Fundamentais completos, macro com vintage histórico, opções e on-chain **não são
recolhidos automaticamente** pelo novo comando. O Codex pode completar fontes
públicas datadas ou marcar os dados como indisponíveis. Kelly exige um histórico
adequado de operações; não é calculado a partir de probabilidades inventadas.

Preços ajustados recolhidos hoje podem incluir revisões. O corte de notícias é
o fim do dia UTC solicitado, podendo incluir notícias posteriores ao fecho da
bolsa. Isto não é um backtest que prove o que era conhecido em cada instante.
Horários semanais não substituem calendários oficiais de feriados e fechos.

HMM, intervalos e caudas são modelos com hipóteses e limitações. Cálculo determinístico
não elimina erros de dados, de modelo ou de interpretação. A leitura de volume G70P
é um conjunto de hipóteses a testar, sem inferir automaticamente intenção ou manipulação.
Uso educativo e de investigação; não constitui aconselhamento financeiro nem
comprovação de rentabilidade.

## Desenvolvimento e histórico

A instalação normal não inclui SDKs de modelos. O extra `legacy-api` conserva o
backend anterior para compatibilidade e testes; não é necessário para utilizar o
fluxo acima. O antigo comando `tradingagents analyze` não é a interface desta versão.
Com o ambiente ativo, `tradingagents MSFT` e `tradingagents-review CAMINHO` são
atalhos dos comandos Python documentados.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,legacy-api]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Para verificar a instalação normal sem SDKs de modelos, num ambiente separado
instalado apenas com `pip install -e .`, executa `python scripts/smoke_local.py`.
O teste usa dados sintéticos e bloqueia a rede; não é uma análise de mercado.

- [Notas da versão e migração](CHANGELOG.md)
- [Validação documentada](docs/VALIDACAO_LOCAL.md)
- [Comparação dos READMEs](docs/REVISAO_README.md)
- [README anterior — arquivo, não instruções atuais](docs/README_LEGADO_API.md)

Mantêm-se a atribuição ao [projeto original Tauric Research](https://github.com/TauricResearch/TradingAgents)
e a [licença do repositório](LICENSE).
