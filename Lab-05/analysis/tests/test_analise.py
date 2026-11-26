import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analise import descritiva, poder, testes
from analise.piloto import run
from analise.sintetico import generate


def _long(groups: dict[str, np.ndarray], metrica: str = "m", paired: bool = False) -> pd.DataFrame:
    rows = []
    for treatment, values in groups.items():
        for i, value in enumerate(values):
            unit = f"u{i}" if paired else f"{treatment}{i}"
            rows.append((treatment, unit, 1, metrica, value))
    return pd.DataFrame(rows, columns=["tratamento", "unidade", "repeticao", "metrica", "valor"])


# ---------------------------------------------------------------- descritiva
def test_validate_rejeita_colunas_ausentes_e_duplicatas():
    with pytest.raises(ValueError, match="Colunas ausentes"):
        descritiva.validate(pd.DataFrame({"valor": [1.0]}))
    df = _long({"A": np.array([1.0, 2.0])})
    with pytest.raises(ValueError, match="duplicadas"):
        descritiva.validate(pd.concat([df, df]))


def test_validate_rejeita_valor_nao_numerico():
    df = _long({"A": np.array([1.0, 2.0])}).astype({"valor": object})
    df.loc[0, "valor"] = "erro"
    with pytest.raises(ValueError, match="finitos"):
        descritiva.validate(df)


def test_summarize_valores_conhecidos():
    df = _long({"A": np.array([1.0, 2.0, 3.0, 4.0, 100.0])})
    row = descritiva.summarize(df).iloc[0]
    assert row["n"] == 5
    assert row["mediana"] == 3.0
    assert row["media"] == pytest.approx(22.0)
    assert row["iqr"] == pytest.approx(2.0)
    assert row["outliers_iqr"] == 1


# ---------------------------------------------------------------- efeitos
def test_holm_valores_conhecidos():
    np.testing.assert_allclose(testes.holm(np.array([0.01, 0.04, 0.03])), [0.03, 0.06, 0.06])


def test_cliffs_delta_extremos_e_simetria():
    x, y = np.array([5.0, 6.0, 7.0]), np.array([1.0, 2.0, 3.0])
    assert testes.cliffs_delta(x, y) == 1.0
    assert testes.cliffs_delta(y, x) == -1.0
    assert testes.cliffs_delta(x, x) == 0.0


def test_rank_biserial_pareado():
    assert testes.rank_biserial_paired(np.array([1.0, 2.0, 3.0])) == 1.0
    assert testes.rank_biserial_paired(np.array([1.0, -1.0])) == 0.0


def test_magnitude_limites():
    assert testes.magnitude("hedges_g", 0.1) == "desprezível"
    assert testes.magnitude("hedges_g", -0.6) == "médio"
    assert testes.magnitude("cliff_delta", 0.5) == "grande"


# ---------------------------------------------------------------- escolha do teste
def test_independente_normal_usa_welch_igual_scipy():
    quantis = stats.norm.ppf((np.arange(1, 41) - 0.5) / 40)  # amostra "perfeitamente" normal
    x, y = 10 + quantis, 11 + 2 * quantis[::-1]
    result = testes.compare(_long({"A": x, "B": y}), "m", pareado=False)
    assert result.teste == "t de Welch"
    assert result.p_valor == pytest.approx(stats.ttest_ind(x, y, equal_var=False).pvalue)
    assert result.efeito < 0  # A menor que B


def test_independente_assimetrico_usa_mann_whitney():
    rng = np.random.default_rng(2)
    x, y = rng.lognormal(0, 1.2, 60), rng.lognormal(0.5, 1.2, 60)
    result = testes.compare(_long({"A": x, "B": y}), "m", pareado=False)
    assert result.teste == "Mann-Whitney U"
    assert result.efeito == pytest.approx(testes.cliffs_delta(x, y))


def test_pareado_usa_mediana_por_unidade_e_wilcoxon_quando_nao_normal():
    rng = np.random.default_rng(3)
    base = rng.lognormal(0, 1, 30)
    df = _long({"A": base, "B": base * 1.3 + rng.exponential(0.5, 30)}, paired=True)
    result = testes.compare(df, "m", pareado=True, metodo="nao_parametrico")
    assert result.teste == "Wilcoxon"
    assert result.n_por_grupo == "A=30, B=30"
    assert result.efeito < 0


def test_k_grupos():
    rng = np.random.default_rng(4)
    groups = {t: rng.normal(mu, 1, 30) for t, mu in zip("ABC", (0, 0.5, 1))}
    assert testes.compare(_long(groups), "m", pareado=False, metodo="parametrico").teste == "ANOVA"
    assert testes.compare(_long(groups), "m", pareado=False, metodo="nao_parametrico").teste == "Kruskal-Wallis"
    assert testes.compare(_long(groups, paired=True), "m", pareado=True).teste == "Friedman"


def test_compare_all_aplica_holm():
    result = testes.compare_all(generate(n_unidades=15, repeticoes=3), pareado=True)
    assert set(result["metrica"]) == {"tempo_ms", "tamanho_kb"}
    assert (result["p_holm"] >= result["p_valor"]).all()


# ---------------------------------------------------------------- poder
def test_fit_lognormal_recupera_parametros():
    rng = np.random.default_rng(5)
    params = poder.fit(rng.lognormal(3.0, 0.4, 20_000))
    assert params.loc == pytest.approx(3.0, abs=0.02)
    assert params.scale == pytest.approx(0.4, abs=0.02)


def test_poder_sob_h0_perto_de_alpha_e_reprodutivel():
    a = poder.GroupParams("normal", 0.0, 1.0)
    result = poder.power_by_n(a, a, [20], n_sims=4_000)
    assert ((result["poder"] - 0.05).abs() < 0.015).all()
    pd.testing.assert_frame_equal(result, poder.power_by_n(a, a, [20], n_sims=4_000))


def test_poder_cresce_com_n_e_pareado_ajuda():
    a, b = poder.GroupParams("lognormal", 5.0, 0.5), poder.GroupParams("lognormal", 4.75, 0.5)
    result = poder.power_by_n(a, b, [10, 40, 100], n_sims=1_000)
    for _, group in result.groupby("teste"):
        assert group["poder"].is_monotonic_increasing
    paired = poder.power_by_n(a, b, [40], pareado=True, rho=0.8, n_sims=1_000)
    assert paired["poder"].min() > result.loc[result["n"] == 40, "poder"].max()
    assert poder.required_n(result, 0.8)["n_necessario"].notna().all()


# ---------------------------------------------------------------- pipeline
def test_run_gera_saidas(tmp_path):
    run(generate(n_unidades=10, repeticoes=3), tmp_path, pareado=True, dist="lognormal", ns=[5, 10], rho=None)
    for name in ("descritivas.csv", "comparacoes.csv", "poder.csv", "n_necessario.csv"):
        assert (tmp_path / name).exists()
    assert (tmp_path / "figuras" / "box_tempo_ms.png").exists()
    assert (tmp_path / "figuras" / "poder_tempo_ms.png").exists()
