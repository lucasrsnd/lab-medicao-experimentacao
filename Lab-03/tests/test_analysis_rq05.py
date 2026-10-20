import gzip
import json

import pytest

pytest.importorskip("scipy")

from lab03.analysis import base, rq05


def item(name, freq, cfr_a, cfr_b, *, stars=100, language="Python"):
    return {
        "metadata": {"full_name": name, "stars": stars, "primary_language": language,
                     "contributor_count": 10, "age_days_at_collection": 1000.0},
        "report": {
            "deployment_frequency": {"releases_per_week": freq, "releases_in_window": 10},
            "lead_time": {"by_release_hours": 48.0, "by_commit_hours": 24.0},
            "ci_failure_rate": None if cfr_a is None else {"rate": cfr_a, "runs_evaluated": 50},
            "delivery_failure_rate": {"rate": cfr_b, "evaluated": 8, "censored": 1},
            "recovery": {"median_hours": 2.0, "episodes_recovered": 3},
            "dora_classification": {"overall": {"category": "High"}},
        },
    }


def dataset(items):
    return {"repositories": items}


def test_base_preserva_ausencia_e_zero(tmp_path):
    rows = base.build_rows(dataset([item("b/y", 0.0, None, 0.0), item("a/x", 1.0, 0.2, None)]))
    assert [r["repositorio"] for r in rows] == ["a/x", "b/y"]
    path = tmp_path / "base.csv"
    base.write_csv(path, rows)
    text = path.read_text(encoding="utf-8").splitlines()
    assert "b/y" in text[2] and ",0.0," in text[2]
    read = base.read_csv(path)
    assert read[0]["cfr_b"] is None and read[1]["cfr_a"] is None
    assert read[1]["deployment_frequency_per_week"] == 0.0 and read[1]["cfr_b"] == 0.0
    assert read[0]["categoria_geral_c1"] == "High"


def test_base_rejeita_duplicata_e_le_gzip(tmp_path):
    with pytest.raises(ValueError):
        base.build_rows(dataset([item("a/x", 1, 0, 0), item("a/x", 2, 0, 0)]))
    path = tmp_path / "d.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(dataset([item("a/x", 1, 0, 0)]), handle)
    out = tmp_path / "out" / "base.csv"
    assert base.main(["--dataset", str(path), "--output", str(out)]) == 0
    assert len(base.read_csv(out)) == 1
    assert base.main(["--dataset", str(tmp_path / "nao.json"), "--output", str(out)]) == 1


def rows_of(items):
    return [base.repository_row(i) for i in items]


def test_spearman_monotonico_e_n_pareado():
    rows = rows_of([item(f"r/{i}", float(i), i / 10, 1 - i / 10) for i in range(1, 8)]
                   + [item("r/aus", 3.0, None, None)])
    analysis = rq05.analyze(rows)
    a, b = analysis["results"]
    assert (a["n"], a["excluded_missing"]) == (7, 1)
    assert a["rho"] == pytest.approx(1.0) and b["rho"] == pytest.approx(-1.0)
    assert a["direction"] == "positiva" and b["direction"] == "negativa"
    assert a["strength"] == "forte" and a["significant_holm"]
    assert a["p_holm"] >= a["p_value"]


def test_variavel_constante_e_n_insuficiente():
    constant = rows_of([item(f"r/{i}", float(i), 0.0, 0.0) for i in range(5)])
    for result in rq05.analyze(constant)["results"]:
        assert result["rho"] is None and result["undefined_reason"] == "variavel_constante"
        assert result["y_zeros"] == 5 and result["p_holm"] is None
    tiny = rows_of([item("r/1", 1.0, 0.1, 0.2), item("r/2", 2.0, 0.3, 0.1)])
    assert rq05.analyze(tiny)["results"][0]["undefined_reason"] == "n_insuficiente"


def test_holm_igual_statsmodels():
    multitest = pytest.importorskip("statsmodels.stats.multitest")
    p = [0.01, 0.04, 0.03, 0.5]
    assert rq05.holm(p) == pytest.approx(list(multitest.multipletests(p, method="holm")[1]))
    assert rq05.holm([None, 0.02]) == [None, 0.02]


def test_median_iqr():
    assert rq05.median_iqr([1, 2, 3, 4, 5]) == {"median": 3, "q1": 2, "q3": 4, "iqr": 2}
    assert rq05.median_iqr([7])["iqr"] == 0 and rq05.median_iqr([])["median"] is None


def test_main_gera_artefatos(tmp_path):
    rows = rows_of([item(f"r/{i}", float(i % 4), (i * 7 % 10) / 10, (i * 3 % 10) / 10)
                    for i in range(12)])
    base.write_csv(tmp_path / "base.csv", rows)
    out = tmp_path / "rq05"
    assert rq05.main(["--base", str(tmp_path / "base.csv"), "--output-dir", str(out)]) == 0
    result = json.loads((out / "rq05_resultados.json").read_text(encoding="utf-8"))
    assert [r["y"] for r in result["results"]] == ["cfr_a", "cfr_b"]
    assert "| CFR (a)" in (out / "rq05_resultados.md").read_text(encoding="utf-8")
    assert (out / "rq05_dispersao.png").stat().st_size > 0
    assert rq05.main(["--base", str(tmp_path / "nao.csv"), "--output-dir", str(out)]) == 1
