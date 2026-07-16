"""
G70P Volume Framework — prompt injection for TradingAgents.

Injects the user's tactical market-reading framework into agent prompts.
Import and use in Market Analyst, Bull/Bear Researcher, Research Manager,
and Professor. Zero tokens — the framework text is part of the system prompt
the LLM receives, not a separate API call.
"""

VOLUME_FRAMEWORK = """
**Framework de Leitura de Volume G70P:**

O volume é o campo de batalha — revela estratégia, tática e intenção. O preço é apenas o resultado infligido. Lê o volume como quem lê o jogo, não o placar.

Princípios:
1. Cada barra começa 0-0. Só o volume decide quem venceu essa barra e com que convicção.
2. Volume baixo não é pausa nem descanso — é engodo. O adversário está escondido, à espera da tua distração.
3. Volume = resultado aceite, não esforço. Muito volume com pouco movimento de preço significa que alguém absorveu do outro lado — essa é a informação real.
4. O vencedor de hoje é o vendedor de amanhã. Quem comprou vai querer vender para lucrar (realização). Quem vendeu vai querer comprar de volta (cobertura). O jogo nunca acaba — só troca de lado.
5. All-in é um tiro no pé. Ninguém ganha sempre. Posições pequenas e consistentes batem apostas grandes e emocionais.
6. Pullback com volume baixo = sem convicção do contra-ataque. Breakout com volume alto = confirmação de que o nível foi aceite. A combinação pullback volume-baixo + entrada no breakout = jogada de qualidade.
7. Compra para cima ou para baixo, o objetivo é sempre o mesmo: lucrar. Para uns lucrarem, outros têm de perder. Pergunta sempre: quem está a perder dinheiro neste momento e o que faria a seguir?

Aplica estes princípios ao interpretar os dados de volume relativo do snapshot verificado. Se o volume não confirma, questiona o sinal — não o ignores.
"""


def inject_volume_framework(prompt: str) -> str:
    """Append the volume framework to an agent's system prompt."""
    return prompt + VOLUME_FRAMEWORK
