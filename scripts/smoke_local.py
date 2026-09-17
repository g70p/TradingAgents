"""Clean-install acceptance: synthetic dossiers, no network or model SDKs."""
import importlib.util
import json
import socket
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from tradingagents.dossier_review import finalize_dossier, verify_evidence
from tradingagents.local import prepare_dossier


def main():
    for module in ("openai", "anthropic", "langchain_core", "langgraph"):
        assert importlib.util.find_spec(module) is None, f"Unexpected model dependency: {module}"

    def blocked(*args, **kwargs):
        raise AssertionError("Network is blocked in clean-install smoke")

    socket.socket.connect = blocked
    socket.create_connection = blocked
    with TemporaryDirectory(prefix="tradingagents-smoke-") as folder:
        root = Path(folder)
        closes = 100 * np.exp(np.cumsum(np.sin(np.arange(40)) * .01))
        pd.DataFrame({"Date": pd.date_range("2025-01-01", periods=40), "Open": closes,
                      "High": closes + 1, "Low": closes - 1, "Close": closes,
                      "Volume": 1000}).to_csv(root / "synthetic.csv", index=False)
        for ticker, kind in (("EDP.LS", "stock"), ("MSFT", "stock"), ("BTC-USD", "crypto")):
            run = prepare_dossier(ticker, "2025-02-09", root, csv=root / "synthetic.csv",
                                  news=False, asset_type=kind)
            manifest = verify_evidence(run)
            assert manifest["analysis_status"] == "pending_codex"
            decision = {"ticker": ticker, "data": "2025-02-09", "rating": "REVIEW",
                        "justificacao": "Ensaio sintético, não recomendação", "limitacoes": ["Dados simulados"]}
            (run / "decisao.json").write_text(json.dumps(decision), encoding="utf-8")
            for name in ("relatorio.md", "professor.md"):
                (run / name).write_text("**Classificação**: REVIEW\n## Análise\nSimulada.\n## Validação\nEnsaio.\n## Ação\nRever.", encoding="utf-8")
            (run / "notas_video.md").write_text("Não apresentar como dados reais.", encoding="utf-8")
            assert finalize_dossier(run)["rating"] == "REVIEW"
    print("PASS: PT/US/crypto dossiers and validation, synthetic data, no network or model SDKs")


if __name__ == "__main__":
    main()
