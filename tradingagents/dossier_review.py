"""Validate a completed Codex dossier without model calls or trading actions."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RATINGS = {"Buy", "Overweight", "Hold", "Underweight", "Sell", "REVIEW"}
EVIDENCE_FILES = {"precos.csv", "noticias.md", "quantitativo.json"}


def verify_evidence(run: Path) -> dict:
    run = Path(run)
    manifest = json.loads((run / "manifesto.json").read_text(encoding="utf-8"))
    hashes = manifest.get("sha256", {})
    if set(hashes) != EVIDENCE_FILES:
        raise ValueError("Lista de ficheiros de evidência inválida")
    for name, digest in hashes.items():
        if hashlib.sha256((run / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Evidência alterada: {name}")
    return manifest


def validate_completion(run: Path) -> dict:
    """Check artifacts before recording completion; human review stays pending."""
    run = Path(run)
    manifest = verify_evidence(run)
    decision = json.loads((run / "decisao.json").read_text(encoding="utf-8"))
    rating = decision.get("rating")
    if rating not in RATINGS:
        raise ValueError("Classificação inválida")
    if decision.get("ticker") != manifest["ticker"] or decision.get("data") != manifest["as_of"]:
        raise ValueError("Ativo/data da decisão não correspondem ao dossier")
    if manifest.get("requires_review") and rating != "REVIEW":
        raise ValueError("Este dossier exige REVIEW")
    if not isinstance(decision.get("justificacao"), str) or not decision["justificacao"].strip():
        raise ValueError("Falta justificação")
    if not isinstance(decision.get("limitacoes"), list) or not decision["limitacoes"]:
        raise ValueError("Faltam limitações")
    artifacts = ["decisao.json", "relatorio.md", "professor.md", "notas_video.md"]
    for name in artifacts[1:]:
        body = (run / name).read_text(encoding="utf-8")
        if not body.strip():
            raise ValueError(f"Ficheiro vazio: {name}")
        if name != "notas_video.md":
            headers = [line.strip() for line in body.splitlines() if line.startswith("**Classificação**:")]
            if headers != [f"**Classificação**: {rating}"]:
                raise ValueError(f"Classificação incoerente: {name}")
            if not all(heading in body for heading in ("## Análise", "## Validação", "## Ação")):
                raise ValueError(f"Falta estrutura AVA: {name}")
    return {
        "status": "completed_codex", "rating": rating,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "human_review": "pending",
        "note": "Validação de estrutura/integridade; não certifica a qualidade financeira da análise.",
        "sha256": {name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in artifacts},
    }


def finalize_dossier(run: Path) -> dict:
    result = validate_completion(run)
    target = Path(run) / "validacao.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)
    return result
