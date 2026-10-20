import csv
import json
from pathlib import Path

import pytest

from lab03.replication import compare as cmp

MAPPING = {
    "original": {"key": "repo", "metrics": {"freq": "df", "cfr": "taxa"},
                 "categories": {"freq": "df_cat", "geral": "overall"}},
    "replicated": {"key": "repository", "metrics": {"freq": "deploys_week", "cfr": "cfr_a"},
                   "categories": {"freq": "freq_category", "geral": "dora"}},
}


def write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def fixtures(tmp_path):
    original = write(tmp_path / "orig.csv", ("repo", "df", "taxa", "df_cat", "overall"), [
        {"repo": "A/x", "df": "2.0", "taxa": "0.10", "df_cat": "High", "overall": "High"},
        {"repo": "b/y", "df": "0", "taxa": "0", "df_cat": "Low", "overall": "Low"},
        {"repo": "c/z", "df": "0", "taxa": "", "df_cat": "Low", "overall": "Medium"},
        {"repo": "d/w", "df": "1,5", "taxa": "NA", "df_cat": "high", "overall": ""},
        {"repo": "e/so-original", "df": "1", "taxa": "0.2", "df_cat": "High", "overall": "High"},
    ])
    replicated = write(tmp_path / "repl.csv",
                       ("repository", "deploys_week", "cfr_a", "freq_category", "dora"), [
        {"repository": "https://github.com/a/x.git", "deploys_week": "2.2", "cfr_a": "0.08",
         "freq_category": "High", "dora": "Medium"},
        {"repository": "b/y/", "deploys_week": "0", "cfr_a": "0", "freq_category": "Low", "dora": "Low"},
        {"repository": "c/z", "deploys_week": "0.5", "cfr_a": "0.3", "freq_category": "Medium",
         "dora": "Medium"},
        {"repository": "d/w", "deploys_week": "", "cfr_a": "0.1", "freq_category": "", "dora": "Low"},
        {"repository": "f/so-replicado", "deploys_week": "1", "cfr_a": "0", "freq_category": "High",
         "dora": "High"},
    ])
    return original, replicated


def run(tmp_path, **kwargs):
    original, replicated = fixtures(tmp_path)
    return cmp.compare(cmp.load_side(original, MAPPING["original"]),
                       cmp.load_side(replicated, MAPPING["replicated"]), **kwargs)


def test_normalizacao_de_chave_e_numeros():
    assert cmp.normalize_key(" https://github.com/Owner/Repo.git/ ") == "owner/repo"
    assert cmp.parse_number("1,5") == 1.5 and cmp.parse_number("0") == 0.0
    assert [cmp.parse_number(v) for v in ("", "NA", "nan", "null", None)] == [None] * 5
    assert cmp.parse_category(" high ") == "High" and cmp.parse_category("") is None


def test_regras_de_comparacao_por_valor():
    assert cmp.compare_value(2.0, 2.2)["delta_rel"] == pytest.approx(0.1)
    assert cmp.compare_value(-2.0, -1.0)["delta_rel"] == pytest.approx(0.5)
    zero = cmp.compare_value(0.0, 0.5)
    assert zero["status"] == "original_zero" and zero["delta_rel"] is None and zero["delta_abs"] == 0.5
    assert cmp.compare_value(0.0, 0.0) == {"original": 0.0, "replicated": 0.0, "status": "ambos_zero",
                                           "delta_abs": 0.0, "delta_rel": 0.0}
    assert cmp.compare_value(None, 1.0)["status"] == "ausente_original"
    assert cmp.compare_value(1.0, None)["delta_abs"] is None


def test_alinhamento_cobertura_e_execucao_parcial(tmp_path):
    result = run(tmp_path, sample_size=30)
    coverage = result["coverage"]
    assert coverage["common"] == 4 and coverage["partial"]
    assert coverage["only_original"] == ["e/so-original"]
    assert coverage["only_replicated"] == ["f/so-replicado"]
    assert coverage["common_over_sample"] == pytest.approx(4 / 30)


def test_resumo_por_metrica(tmp_path):
    result = run(tmp_path, tolerance=0.15)
    freq, cfr = result["metrics"]["freq"], result["metrics"]["cfr"]
    assert freq["statuses"] == {"comparavel": 1, "ambos_zero": 1, "original_zero": 1,
                                "ausente_original": 0, "ausente_replicado": 1}
    assert freq["n_comparable"] == 2 and freq["n_with_both"] == 3
    assert freq["delta_rel"]["median"] == pytest.approx(0.05)
    assert freq["within_tolerance"] == 1.0
    assert cfr["statuses"]["ausente_original"] == 2
    assert cfr["n_comparable"] == 2 and cfr["abs_delta_rel_median"] == pytest.approx(0.1)


def test_categorias_mesma_e_transicoes(tmp_path):
    categories = run(tmp_path)["categories"]
    assert categories["freq"]["n"] == 3 and categories["freq"]["same"] == 2
    assert categories["freq"]["transitions"] == {"High -> High": 1, "Low -> Low": 1, "Low -> Medium": 1}
    geral = categories["geral"]
    assert (geral["n"], geral["same"]) == (3, 2) and geral["same_proportion"] == pytest.approx(2 / 3)


def test_erros_de_entrada(tmp_path):
    original, _ = fixtures(tmp_path)
    with pytest.raises(ValueError, match="colunas ausentes"):
        cmp.load_side(original, {"key": "repo", "metrics": {"x": "inexistente"}})
    duplicated = write(tmp_path / "dup.csv", ("repo", "df"), [{"repo": "a/x", "df": "1"},
                                                            {"repo": "A/X", "df": "2"}])
    with pytest.raises(ValueError, match="duplicado"):
        cmp.load_side(duplicated, {"key": "repo", "metrics": {"f": "df"}})
    text = write(tmp_path / "txt.csv", ("repo", "df"), [{"repo": "a/x", "df": "rápido"}])
    with pytest.raises(ValueError, match="não numérico"):
        cmp.load_side(text, {"key": "repo", "metrics": {"f": "df"}})
    with pytest.raises(ValueError, match="difere"):
        cmp.validate_mapping({"original": {"key": "k", "metrics": {"a": "a"}},
                              "replicated": {"key": "k", "metrics": {"b": "b"}}})
    with pytest.raises(ValueError, match="replicated.key"):
        cmp.validate_mapping({"original": {"key": "k"}})


def test_main_gera_artefatos(tmp_path):
    original, replicated = fixtures(tmp_path)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps(MAPPING), encoding="utf-8")
    out = tmp_path / "out"
    args = ["--original", str(original), "--replicated", str(replicated), "--mapping", str(mapping),
            "--output-dir", str(out)]
    assert cmp.main(args) == 0
    assert json.loads((out / "comparacao.json").read_text(encoding="utf-8"))["coverage"]["common"] == 4
    assert "execução parcial" in (out / "comparacao.md").read_text(encoding="utf-8")
    tex = (out / "comparacao_tabela.tex").read_text(encoding="utf-8")
    assert "\\begin{tabular}" in tex and "geral (categoria)" in tex and "66{,}7\\%" in tex
    rows = list(csv.DictReader((out / "comparacao_repositorios.csv").open(encoding="utf-8")))
    assert len(rows) == 4 * 4
    assert cmp.main(args[:-2] + ["--output-dir", str(out), "--sample-size", "4"]) == 0
    assert "parcial" not in (out / "comparacao.md").read_text(encoding="utf-8")
    mapping.write_text("{}", encoding="utf-8")
    assert cmp.main(args) == 1


def test_mapeamento_exemplo_compara_base_consigo_mesma(tmp_path):
    root = Path(__file__).parents[1]
    mapping = json.loads((root / "config" / "replicacao-mapeamento.exemplo.json").read_text(encoding="utf-8"))
    cmp.validate_mapping(mapping)
    base = write(tmp_path / "base.csv", ("repositorio", "deployment_frequency_per_week",
                                         "lead_time_a_hours", "cfr_a", "recovery_hours",
                                         "categoria_geral_c1"),
                 [{"repositorio": "a/x", "deployment_frequency_per_week": "1", "lead_time_a_hours": "",
                   "cfr_a": "0", "recovery_hours": "3", "categoria_geral_c1": "High"}])
    result = cmp.compare(cmp.load_side(base, mapping["original"]),
                         cmp.load_side(base, mapping["replicated"]), sample_size=1)
    assert result["metrics"]["frequencia"]["delta_rel"]["median"] == 0.0
    assert result["metrics"]["lead_time"]["statuses"]["ausente_original"] == 1
    assert result["categories"]["geral"]["same_proportion"] == 1.0
