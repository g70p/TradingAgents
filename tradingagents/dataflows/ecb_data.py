"""ECB (Banco Central Europeu) — dados macroeconómicos gratuitos.

Substitui o FRED (que exige API key). Usa a API pública do ECB,
que não requer autenticação. Focado em indicadores europeus e globais.

Fontes:
  - ECB SDMX REST API: taxas de juro, inflação, PIB
  - ECB Statistical Data Warehouse: dados cambiais e monetários
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# ECB SDMX API — taxa de juro directora, inflação HICP
# ═══════════════════════════════════════════════════════════════════════════════

_ECB_SDMX_BASE = "https://data-api.ecb.europa.eu/service/data"


def _fetch_ecb_json(dataset: str, params: str, timeout: int = 10) -> dict | None:
    """Fetch data from ECB SDMX JSON API."""
    url = f"{_ECB_SDMX_BASE}/{dataset}?format=jsondata&{params}"
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "TradingAgents/2.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
        logger.debug("ECB API failed for %s: %s", dataset, e)
        return None


def _extract_latest_value(data: dict) -> tuple[str, float] | None:
    """Extract the most recent observation from ECB SDMX response."""
    try:
        series = data.get("dataSets", [{}])[0].get("series", {})
        structure = data.get("structure", {}).get("dimensions", {}).get("observation", [])

        if not series:
            return None

        # Get the first (and usually only) series key
        obs = None
        for key in series:
            obs = series[key].get("observations", {})
            if obs:
                break

        if not obs:
            return None

        # Get the last time period
        times = sorted(obs.keys(), reverse=True)
        if not times:
            return None

        last_time = times[0]
        value = obs[last_time][0]

        # Convert observation index to actual date
        time_values = None
        for dim in structure:
            if dim.get("name") == "TIME_PERIOD":
                time_values = dim.get("values", [])
                break

        if time_values and last_time.isdigit():
            idx = int(last_time)
            if idx < len(time_values):
                last_time = time_values[idx].get("id", last_time)

        return (last_time, float(value))
    except (KeyError, IndexError, ValueError, TypeError) as e:
        logger.debug("ECB extraction failed: %s", e)
        return None


def get_ecb_interest_rate() -> str:
    """Taxa de juro directora do BCE (deposit facility rate).

    Dataset: FM.D.U2.EUR.4F.KR.DFR.LEV
    """
    data = _fetch_ecb_json(
        "FM/M.U2.EUR.4F.KR.DFR.LEV",
        "startPeriod=2024-01-01&detail=dataonly",
    )
    if not data:
        return _ecb_fallback("taxa de juro BCE")

    result = _extract_latest_value(data)
    if not result:
        return _ecb_fallback("taxa de juro BCE")

    date, rate = result
    return (
        f"🏦 **Taxa de Juro BCE (Deposit Facility):**\n"
        f"- **Data**: {date}\n"
        f"- **Taxa**: {rate:.2f}%\n"
        f"- **Fonte**: BCE SDMX (gratuito, sem API key)"
    )


def get_ecb_inflation() -> str:
    """Inflação HICP da Zona Euro (Harmonised Index of Consumer Prices).

    Dataset: ICP.M.U2.N.000000.4.ANR
    """
    data = _fetch_ecb_json(
        "ICP/M.U2.N.000000.4.ANR",
        "startPeriod=2024-01-01&detail=dataonly",
    )
    if not data:
        return _ecb_fallback("inflação Zona Euro")

    result = _extract_latest_value(data)
    if not result:
        return _ecb_fallback("inflação Zona Euro")

    date, rate = result

    signal = (
        "⚠️ Acima da meta de 2%" if rate > 2.5
        else "🟢 Próximo da meta" if rate <= 2.5 and rate >= 1.5
        else "🔵 Abaixo da meta"
    )

    return (
        f"📊 **Inflação Zona Euro (HICP, anual):**\n"
        f"- **Data**: {date}\n"
        f"- **Taxa**: {rate:.1f}% {signal}\n"
        f"- **Fonte**: BCE SDMX (gratuito, sem API key)"
    )


def get_ecb_exchange_rate(currency: str = "USD") -> str:
    """Taxa de câmbio EUR/USD do BCE.

    Dataset: EXR.M.USD.EUR.SP00.A
    """
    data = _fetch_ecb_json(
        f"EXR/M.{currency}.EUR.SP00.A",
        "startPeriod=2024-06-01&detail=dataonly",
    )
    if not data:
        return ""

    result = _extract_latest_value(data)
    if not result:
        return ""

    date, rate = result
    return (
        f"💱 **EUR/{currency} (BCE):**\n"
        f"- **Data**: {date}\n"
        f"- **Cotação**: {rate:.4f}\n"
        f"- **Fonte**: BCE SDMX (gratuito)"
    )


def get_ecb_macro_summary() -> str:
    """Resumo macroeconómico europeu agregado (para injeção em prompts)."""
    parts = ["## 🏦 Dados Macroeconómicos (BCE)\n"]

    rate = get_ecb_interest_rate()
    if "indisponível" not in rate.lower():
        parts.append(rate)
        parts.append("")

    inflation = get_ecb_inflation()
    if "indisponível" not in inflation.lower():
        parts.append(inflation)
        parts.append("")

    fx = get_ecb_exchange_rate("USD")
    if fx:
        parts.append(fx)
        parts.append("")

    if len(parts) == 1:
        return "⚠️ Dados macro BCE indisponíveis (tenta mais tarde).\n"

    parts.append(
        "**Interpretação para Trading:**\n"
        "- Juros altos → pressão sobre ações de crescimento e cripto\n"
        "- Inflação acima da meta → BCE mantém ou sobe juros\n"
        "- EUR fraco → exportadoras europeias beneficiadas\n"
        "- EUR forte → pressão sobre exportadoras, alívio na inflação importada\n"
        "\n_Fonte: BCE SDMX API — gratuito, sem autenticação._"
    )

    return "\n".join(parts)


def get_ecb_macro_indicators(*args, **kwargs) -> str:
    """Wrapper compatível com a interface de vendors para dados macro ECB."""
    return get_ecb_macro_summary()


def _ecb_fallback(indicator: str) -> str:
    """Fallback quando a API ECB falha."""
    return f"⚠️ Dados de {indicator} indisponíveis (ECB API não respondeu — tenta mais tarde)."
