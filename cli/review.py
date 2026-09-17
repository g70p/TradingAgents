"""Validate artifacts produced in the user's Codex session."""
import argparse
from pathlib import Path

from tradingagents.dossier_review import finalize_dossier


def main():
    parser = argparse.ArgumentParser(description="Validar um dossier concluído no Codex")
    parser.add_argument("dossier", type=Path)
    args = parser.parse_args()
    try:
        result = finalize_dossier(args.dossier)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Validação falhou: {exc}\n")
    print(f"Validado: {result['rating']}. Revisão humana pendente.")


if __name__ == "__main__":
    main()
