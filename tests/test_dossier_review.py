import hashlib
import json

import pytest

from tradingagents.dossier_review import EVIDENCE_FILES, finalize_dossier, verify_evidence


@pytest.fixture
def dossier(tmp_path):
    for name in EVIDENCE_FILES:
        (tmp_path / name).write_bytes(b"fixture")
    manifest = {"ticker": "MSFT", "as_of": "2025-01-01", "requires_review": True,
                "sha256": {name: hashlib.sha256(b"fixture").hexdigest() for name in EVIDENCE_FILES}}
    (tmp_path / "manifesto.json").write_text(json.dumps(manifest))
    decision = {"ticker": "MSFT", "data": "2025-01-01", "rating": "REVIEW",
                "justificacao": "Dados insuficientes", "limitacoes": ["Sem preços"]}
    (tmp_path / "decisao.json").write_text(json.dumps(decision))
    for name in ["relatorio.md", "professor.md"]:
        (tmp_path / name).write_text("**Classificação**: REVIEW\n## Análise\nTeste\n## Validação\nTeste\n## Ação\nRever.", encoding="utf-8")
    (tmp_path / "notas_video.md").write_text("Dados simulados", encoding="utf-8")
    return tmp_path


def test_resume_and_finalize_preserves_evidence(dossier):
    before = (dossier / "manifesto.json").read_bytes()
    first = finalize_dossier(dossier)
    second = finalize_dossier(dossier)
    assert first["sha256"] == second["sha256"]
    assert second["status"] == "completed_codex"
    assert second["human_review"] == "pending"
    assert (dossier / "manifesto.json").read_bytes() == before


def test_tampered_prices_block_completion(dossier):
    (dossier / "precos.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="alterada"):
        finalize_dossier(dossier)
    assert not (dossier / "validacao.json").exists()


def test_professor_disagreement_blocks_completion(dossier):
    path = dossier / "professor.md"
    path.write_text(path.read_text(encoding="utf-8").replace("REVIEW", "Buy"), encoding="utf-8")
    with pytest.raises(ValueError, match="incoerente"):
        finalize_dossier(dossier)


def test_required_review_cannot_be_overridden(dossier):
    path = dossier / "decisao.json"
    value = json.loads(path.read_text())
    value["rating"] = "Buy"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="exige REVIEW"):
        finalize_dossier(dossier)


def test_manifest_cannot_request_arbitrary_paths(dossier):
    path = dossier / "manifesto.json"
    value = json.loads(path.read_text())
    value["sha256"]["../secret"] = "anything"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Lista"):
        verify_evidence(dossier)
