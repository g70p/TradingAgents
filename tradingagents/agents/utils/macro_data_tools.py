from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_macro_indicators(
    indicator: Annotated[
        str,
        "Indicador macroeconómico. Com a fonte BCE (padrão), este parâmetro é "
        "ignorado — a ferramenta devolve sempre o resumo completo: taxa de juro "
        "diretora BCE, inflação HICP Zona Euro, e câmbio EUR/USD.",
    ],
    curr_date: Annotated[str, "Data atual em formato yyyy-mm-dd; fim da janela de análise"],
    look_back_days: Annotated[
        int | None, "Janela temporal em dias; omitir para janela de 1 ano"
    ] = None,
) -> str:
    """
    Obtém indicadores macroeconómicos da Zona Euro via BCE (Banco Central Europeu):
    taxa de juro diretora (deposit facility), inflação HICP, e câmbio EUR/USD.
    Devolve os valores mais recentes com interpretação para trading.
    Fonte: BCE SDMX API — gratuita, sem autenticação.

    Args:
        indicator (str): Ignorado com a fonte ECB (devolve sempre o resumo completo)
        curr_date (str): Data atual em yyyy-mm-dd
        look_back_days (int): Janela temporal; omitir para 1 ano

    Returns:
        str: Relatório formatado em markdown com os indicadores BCE
    """
    return route_to_vendor("get_macro_indicators", indicator, curr_date, look_back_days)
