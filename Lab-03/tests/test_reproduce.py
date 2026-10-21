"""#126/#133: reprodução única das análises e regressão sobre o dataset congelado."""

import json
from pathlib import Path

import pytest

pytest.importorskip("scipy")
pytest.importorskip("matplotlib")
pytest.importorskip("sklearn")

from lab03.analysis import reproduce  # noqa: E402

LAB03 = Path(__file__).parents[1]
MANIFEST = LAB03 / "analysis" / reproduce.MANIFEST_NAME


def manifest(outputs, inputs=None):
    return {
        "inputs": inputs or {},
        "outputs": {
            name: {"canonical_sha256": digest, "stable": stable}
            for name, (digest, stable) in outputs.items()
        },
    }


def test_compare_aceita_manifestos_iguais_e_ignora_saida_instavel():
    esperado = manifest({"a.csv": ("1", True), "f.png": ("x", False)})
    obtido = manifest({"a.csv": ("1", True), "f.png": ("y", False)})
    assert reproduce.compare(esperado, obtido) == []


def test_compare_aponta_ausente_diferente_e_nova():
    esperado = manifest({"a.csv": ("1", True), "b.csv": ("2", True)})
    obtido = manifest({"a.csv": ("9", True), "c.csv": ("3", True)})
    assert sorted(reproduce.compare(esperado, obtido)) == [
        "ausente: b.csv",
        "diferente: a.csv",
        "nova saída fora do manifesto: c.csv",
    ]


def test_compare_aponta_entrada_congelada_alterada():
    esperado = manifest({}, {"data/x": "1"})
    assert reproduce.compare(esperado, manifest({}, {"data/x": "2"})) == [
        "entradas congeladas diferem do manifesto"
    ]


def test_hash_canonico_de_json_ignora_ruido_de_ultimo_digito(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"p": 0.3188029654733097}), encoding="utf-8")
    b.write_text(json.dumps({"p": 0.31880296547330966}), encoding="utf-8")
    assert reproduce.sha256(a) != reproduce.sha256(b)
    assert reproduce.canonical_sha256(a) == reproduce.canonical_sha256(b)


def test_hash_canonico_de_json_percebe_mudanca_real(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"rho": 0.151}), encoding="utf-8")
    b.write_text(json.dumps({"rho": 0.152}), encoding="utf-8")
    assert reproduce.canonical_sha256(a) != reproduce.canonical_sha256(b)


def test_manifesto_versionado_nao_tem_caminho_pessoal_nem_segredo():
    texto = MANIFEST.read_text(encoding="utf-8")
    for proibido in ("C:\\", "C:/", "/Users/", "/home/", "ghp_", "github_pat_"):
        assert proibido not in texto


def test_reproducao_completa_bate_com_o_manifesto_versionado(capsys):
    """Regressão: qualquer mudança nas análises ou no dataset congelado aparece aqui."""
    assert reproduce.main(["--output", str(LAB03 / "analysis"), "--check"]) == 0
    assert "idêntica" in capsys.readouterr().out
