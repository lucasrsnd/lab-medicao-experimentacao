import csv
import json

import pytest

pytest.importorskip("sklearn")

from lab03.analysis import cfr_b_validation as validation


def repo(name, verdicts):
    """verdicts: {tag: corrective}; release_id = 100 + posição."""
    tags = list(verdicts)
    return {
        "metadata": {"full_name": name},
        "report": {
            "catalog": {"releases": [{"tag": t, "id": 100 + i} for i, t in enumerate(tags)]},
            "delivery_failure_rate": {
                "heuristic_version": "v2",
                "verdicts": [{"tag": t, "corrective": c} for t, c in verdicts.items()],
            },
        },
    }


def sample(name, tag, release_id):
    return {"repositorio": name, "tag": tag, "release_id": str(release_id)}


def label(name, tag, value, obs=""):
    return {"repositorio": name, "tag": tag, "e_corretiva": value, "observacoes": obs}


DATASET = {"repositories": [repo("a/x", {"v1": True, "v2": False, "v3": True}),
                            repo("b/y", {"v1": False})]}
SAMPLE = [sample("a/x", "v1", 100), sample("a/x", "v2", 101), sample("a/x", "v3", 999),
          sample("b/y", "v1", 100), sample("c/fora", "v1", 100)]
B = [label("a/x", "v1", "sim"), label("a/x", "v2", "sim"), label("a/x", "v3", "nao"),
     label("b/y", "v1", "nao"), label("c/fora", "v1", "sim")]
A = [label(r["repositorio"], r["tag"], "sim", "[rascunho IA] x") for r in B]


def test_exclui_fora_do_snapshot_e_release_id_divergente():
    matched, excluded = validation.match_sample(DATASET, SAMPLE)
    assert [(r["repositorio"], r["tag"]) for r in matched] == [("a/x", "v1"), ("a/x", "v2"), ("b/y", "v1")]
    assert excluded == {"release_id_diferente": 1, "repositorio_fora_do_snapshot": 1}


def test_metricas_contra_b_e_llm_auxiliar():
    result = validation.analyze(DATASET, SAMPLE, B, A)
    h = result["heuristic_vs_b"]
    # B: sim, sim, nao; heurística: sim, nao, nao
    assert h["confusion_matrix"]["values"] == [[1, 0], [1, 1]]
    assert h["precision"] == 1.0 and h["recall"] == 0.5
    assert h["confusion_matrix"]["rows_are_reference"] == "rotulo_b"
    assert result["sample"]["evaluated_releases"] == 3
    assert result["sample"]["a_rows_marked_ai_draft"] == 3
    assert result["auxiliary_llm"]["agreement_b_vs_llm"] == pytest.approx(2 / 3)


def test_rotulo_ausente_falha():
    with pytest.raises(ValueError):
        validation.analyze(DATASET, SAMPLE, B[:1], A)


def test_wilson_e_kappa():
    assert validation.wilson(0, 0) is None
    low, high = validation.wilson(26, 111)
    assert low < 26 / 111 < high
    assert validation.cohen_kappa(["sim", "nao"], ["sim", "nao"]) == 1.0
    assert validation.cohen_kappa(["sim", "sim"], ["sim", "sim"]) is None


def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_main_grava_saidas(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps(DATASET), encoding="utf-8")
    for name, rows in (("s.csv", SAMPLE), ("b.csv", B), ("a.csv", A)):
        write(tmp_path / name, rows)
    out = tmp_path / "out"
    args = ["--dataset", str(tmp_path / "d.json"), "--sample", str(tmp_path / "s.csv"),
            "--rater-b", str(tmp_path / "b.csv"), "--rater-a-llm", str(tmp_path / "a.csv"),
            "--output-dir", str(out)]
    assert validation.main(args) == 0
    result = json.loads((out / "resultados.json").read_text(encoding="utf-8"))
    assert "_releases" not in result and set(result["input_sha256"]) == {
        "dataset", "sample", "rater_b", "rater_a_llm"}
    assert len((out / "releases.csv").read_text(encoding="utf-8").splitlines()) == 4
    assert validation.main(args[:-2] + ["--output-dir", str(out), "--sample", "nao.csv"]) == 1
