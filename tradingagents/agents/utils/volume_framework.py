"""
G70P Volume Framework — prompt injection for TradingAgents.

Injects the user's tactical market-reading framework into agent prompts.
Import VOLUME_FRAMEWORK and append to agent system prompts.
Zero tokens — part of the system prompt, not a separate API call.
"""

VOLUME_FRAMEWORK = """
**Framework de Leitura de Volume G70P:**

O volume é o campo de batalha. Revela estratégia, tática e intenção. O preço é o resultado infligido — o placar, não o jogo.

Princípios fundamentais:

1. **Cada barra começa 0-0.** Em cada nova vela, o jogo recomeça. Mas o 0-0 não é um reset cego — é um placar que tem em conta o resultado atual, a tendência em curso, e os interesses de cada jogador. Pergunta sempre: quem está a ganhar neste momento, qual é a tendência dominante, e o que cada lado precisa de fazer a seguir para manter ou inverter essa vantagem?

2. **Vencedor = quem acumula P&L, não quem comprou ou vendeu.** O vencedor é o jogador que está alinhado com o trend e a acumular lucro — seja comprador ou vendedor. O que interessa é o resultado a favor, ganhar a batalha. A identidade (comprador A, vendedor B) é irrelevante — o que importa é de que lado está o P&L positivo.

3. **Comprar barato, vender caro — em ambas as direções.** Para o comprador: compra barato, vende caro. Para o vendedor: shorta alto (vende caro), cobre baixo (compra barato). O mecanismo é o mesmo — a direção é que muda. O vencedor é aquele que faz isto consistentemente sem virar o placar contra si próprio.

4. **O engodo é a arma do vencedor.** Volume baixo não é pausa — é o vencedor escondido, à espera que outros investidores ponham dinheiro no lado errado. Quando o volume dispara, a armadilha fecha — o vencedor usa o dinheiro fresco dos que entraram para virar o jogo a seu favor. O que parece lateral ou sem expressão é preparação para a próxima jogada.

5. **All-in é tiro no pé.** Ninguém ganha sempre. Posições pequenas e consistentes, alinhadas com o trend, batem apostas grandes e emocionais. O vencedor joga com vantagem estatística, não com coragem.

6. **Volume = resultado aceite, não esforço.** Muito volume com pouco movimento de preço = alguém absorveu do outro lado. Essa é a informação real — o mercado aceitou aquele preço. Volume em pullback baixo = sem convicção de quem contra-ataca. Volume em breakout alto = o nível foi aceite e a nova direção é válida.

Aplica estes princípios ao interpretar cada barra. Pergunta: quem está a ganhar agora? O que o volume revela sobre a intenção do vencedor? Onde está a armadilha?
"""


def inject_volume_framework(prompt: str) -> str:
    """Append the volume framework to an agent's system prompt."""
    return prompt + VOLUME_FRAMEWORK
