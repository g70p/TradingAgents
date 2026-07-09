# TradingAgents/graph/reflection.py

from typing import Any


class Reflector:
    """Handles reflection on trading decisions."""

    def __init__(self, quick_thinking_llm: Any):
        """Initialize the reflector with an LLM."""
        self.quick_thinking_llm = quick_thinking_llm
        self.log_reflection_prompt = self._get_log_reflection_prompt()

    def _get_log_reflection_prompt(self) -> str:
        """Concise prompt for reflect_on_final_decision (Phase B log entries).

        Produces 2-4 sentences of plain prose — compact enough to be re-injected
        into future agent prompts without bloating the context window.
        """
        return (
            "És um analista de trading a rever a tua própria decisão passada agora que o resultado é conhecido.\n"
            "Escreve exatamente 2 a 4 frases em prosa simples (sem bullets, sem cabeçalhos, sem markdown).\n\n"
            "Cobre por ordem:\n"
            "1. A previsão direcional estava correta? (cita o valor de alpha)\n"
            "2. Que parte da tese de investimento se confirmou ou falhou?\n"
            "3. Uma lição concreta a aplicar na próxima análise semelhante.\n\n"
            "Sê específico e conciso. O teu resultado será armazenado literalmente num registo de decisões "
            "e relido por futuros analistas, por isso cada palavra tem de justificar o seu lugar."
        )

    def reflect_on_final_decision(
        self,
        final_decision: str,
        raw_return: float,
        alpha_return: float,
        benchmark_name: str = "SPY",
    ) -> str:
        """Single reflection call on the final trade decision with outcome context.

        Used by Phase B deferred reflection. The final_trade_decision already
        synthesises all analyst insights, so no separate market context is needed.
        ``benchmark_name`` is the label used for the alpha line (e.g. ``"SPY"``
        for US tickers, ``"^N225"`` for ``.T`` listings); defaults to SPY for
        callers that haven't been updated to thread the benchmark through.
        """
        messages = [
            ("system", self.log_reflection_prompt),
            (
                "human",
                (
                    f"Retorno bruto: {raw_return:+.1%}\n"
                    f"Alpha vs {benchmark_name}: {alpha_return:+.1%}\n\n"
                    f"Decisão Final:\n{final_decision}"
                ),
            ),
        ]
        return self.quick_thinking_llm.invoke(messages).content
