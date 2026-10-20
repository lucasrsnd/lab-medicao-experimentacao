import json

import pytest

pytest.importorskip("scipy")

from lab03.analysis import base, rq06


def row(name, *, language="Python", stars=100.0, contributors=10.0, freq=1.0, lead=24.0,
        cfr=0.1, recovery=2.0):
    return {"repositorio": name, "linguagem": language, "estrelas": stars,
            "contribuidores": contributors, "deployment_frequency_per_week": freq,
            "lead_time_a_hours": lead, "cfr_a": cfr, "recovery_hours": recovery}


def test_quartis_com_empate_no_corte_ficam_no_inferior():
    rows = [row(f"r/{i}", stars=float(v)) for i, v in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9])]
    groups, cuts = rq06.quartile_groups(rows, "estrelas")
    assert cuts == [3.0, 5.0, 7.0]
    assert [groups[f"r/{i}"] for i in range(9)] == ["Q1"] * 3 + ["Q2"] * 2 + ["Q3"] * 2 + ["Q4"] * 2


def test_linguagens_raras_agrupadas_e_ausentes_ignoradas():
    rows = ([row(f"py/{i}") for i in range(10)] + [row("go/1", language="Go"),
            row("rs/1", language="Rust"), row("x/1", language=None)])
    groups, pooled = rq06.language_groups(rows)
    assert pooled == ["Go", "Rust"]
    assert groups["go/1"] == groups["rs/1"] == "Outras" and "x/1" not in groups


def test_kruskal_epsilon_e_mann_whitney_cliff():
    from scipy.stats import kruskal

    samples = {"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0], "C": [7.0, 8.0, 9.0]}
    result = rq06.compare(samples)
    h = kruskal(*samples.values()).statistic
    assert result["test"] == "kruskal-wallis" and result["n"] == 9
    assert result["effect_value"] == pytest.approx(h / 8) and result["effect_size"] == "grande"
    two = rq06.compare({"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0], "vazio": []})
    assert two["test"] == "mann-whitney" and two["k"] == 2
    assert two["effect_value"] == pytest.approx(-1.0) and two["effect_size"] == "grande"


def test_indefinidos_sem_p_valor():
    assert rq06.compare({"A": [1.0, 2.0]})["undefined_reason"] == "menos_de_dois_grupos"
    constant = rq06.compare({"A": [0.0, 0.0], "B": [0.0, 0.0]})
    assert constant["undefined_reason"] == "metrica_constante" and constant["p_value"] is None


def test_rotulos_de_efeito():
    assert [rq06.epsilon_label(v) for v in (0.005, 0.05, 0.1, 0.3)] == [
        "desprezível", "pequeno", "médio", "grande"]
    assert [rq06.cliff_label(v) for v in (0.1, -0.2, 0.4, -0.5)] == [
        "desprezível", "pequeno", "médio", "grande"]


def sample_rows():
    rows = []
    for i in range(24):
        language = ("Python", "Go", "Rust")[i % 3]
        rows.append(row(f"r/{i}", language=language, stars=float(100 + i), contributors=float(i),
                        freq=float(i % 5), lead=None if i == 0 else float(10 * (i % 3) + i),
                        cfr=(i % 4) / 10, recovery=float(i)))
    return rows


def test_analise_familia_holm_e_ausencias(monkeypatch):
    monkeypatch.setattr(rq06, "MIN_LANGUAGE_GROUP", 5)
    analysis = rq06.analyze(sample_rows())
    assert len(analysis["tests"]) == 12 and analysis["family_size"] == 12
    lead = next(t for t in analysis["tests"]
                if t["factor"] == "linguagem" and t["metric"] == "lead_time_a_hours")
    assert lead["n"] == 23 and sum(g["n"] for g in lead["groups"]) == 23
    assert all(t["p_holm"] >= t["p_value"] for t in analysis["tests"])
    assert analysis["factors"]["estrelas"]["sizes"] == {"Q1": 6, "Q2": 6, "Q3": 6, "Q4": 6}
    assert analysis["factors"]["linguagem"]["pooled_into_other"] == []


def test_main_gera_artefatos(tmp_path):
    path = tmp_path / "base.csv"
    rows = [dict(base.repository_row({"metadata": {"full_name": r["repositorio"]}, "report": {}}),
                 **r) for r in sample_rows()]
    base.write_csv(path, rows)
    out = tmp_path / "rq06"
    assert rq06.main(["--base", str(path), "--output-dir", str(out)]) == 0
    result = json.loads((out / "rq06_resultados.json").read_text(encoding="utf-8"))
    assert {t["factor"] for t in result["tests"]} == set(rq06.FACTORS)
    text = (out / "rq06_resultados.md").read_text(encoding="utf-8")
    assert "Quartis de estrelas" in text and "Outras" in text
    assert (out / "rq06_grupos.csv").read_text(encoding="utf-8").startswith("fator,metrica,grupo")
    assert rq06.main(["--base", str(tmp_path / "nao.csv"), "--output-dir", str(out)]) == 1
