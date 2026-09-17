# Revisão do README para publicação — 17-09-2026

Comparado com o README publicado na branch `g70p`, commit `3e94006daa4ca6182a3f6b8aa5b1399811c1524e`, blob `531bdf5536e536fd93884691ace6f157f1f068c4`, obtido através da integração GitHub. Comparado também com o README local da migração inicial.

| Antes | Alteração final | Motivo |
|---|---|---|
| DeepSeek e `.env` obrigatórios | Codex autenticado e instalação sem SDKs de modelos | Corresponder ao uso solicitado |
| Clone sem branch | Clone/ZIP explícitos de `g70p` | Evitar descarregar a versão errada |
| Instalação focada em shell Unix | Comandos completos Windows e macOS/Linux | Eliminar adaptações implícitas |
| Menu `analyze` e grafo API como início | Pedido em linguagem natural e `main.py` | Corresponder à interface publicada |
| Arquitetura e lista de funcionalidades sem separar disponibilidade | Fluxo de papéis e cobertura real do coletor | Não anunciar fontes que não são recolhidas automaticamente |
| “Zero risco de alucinação” e Bachelier | Projeção lognormal e limites dos modelos | Descrever o cálculo existente sem promessas indevidas |
| Saída pouco explicada | Tabela de ficheiros e distinção recolha/análise/validação | Tornar o resultado verificável |
| Retoma e erros sem instruções completas | Retoma por dossier, atualização e troubleshooting | Apoiar um utilizador sem contexto desta conversa |

Preservados: identidade G70P, PT-PT, AVA, debate, gestão de risco, Professor, atribuição ao original e licença. A documentação antiga foi arquivada explicitamente. Testes e verificação de instalação constam do registo de validação e do workflow CI.
