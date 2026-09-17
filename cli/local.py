"""Default CLI: prepare evidence for Codex, without LLM APIs."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="TradingAgents local + Codex, sem chaves API de IA")
    parser.add_argument("ticker", help="Símbolo Yahoo Finance, por exemplo MSFT ou BTC-USD")
    parser.add_argument("--date", default=date.today().isoformat(), help="Data limite YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    parser.add_argument("--csv", type=Path, help="OHLCV local: Date,Open,High,Low,Close,Volume")
    parser.add_argument("--no-news", action="store_true", help="Não consultar notícias online")
    parser.add_argument("--asset-type", choices=["stock", "crypto"], default="stock")
    args = parser.parse_args(argv)
    from tradingagents.local import prepare_dossier

    try:
        run = prepare_dossier(args.ticker, args.date, args.output, csv=args.csv,
                              news=not args.no_news, asset_type=args.asset_type)
    except Exception as exc:
        parser.exit(1, f"Não foi possível preparar o dossier: {exc}\n")
    print(f"Dossier: {run.resolve()}")
    print("No Codex, pede: Lê ANALISAR_NO_CODEX.md desta pasta e executa a análise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
