import json

import numpy as np
import pandas as pd
import pytest

from lab04 import real_results
from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS
from lab04.permutation import permutation_null, permutation_pvalue
from lab04.plots import poder_n


def sample(seed=0, rho=0.5, n=30):
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal((0, 0), ((1, rho), (rho, 1)), size=n)
    return pd.DataFrame({"loc": np.round(np.exp(4 + z[:, 0])) + 1, "defects": np.floor(np.exp(z[:, 1]))})


def test_permutation_pvalue_counts_extremes_and_is_never_zero():
    null = np.array([-3.0, -1.0, 0.5, 2.0, 4.0])
    assert permutation_pvalue(null, 2.0) == pytest.approx((3 + 1) / 6)
    assert permutation_pvalue(null, 10.0) == pytest.approx(1 / 6)


def test_real_tests_add_permutation_pvalue_close_to_t_for_spearman():
    rows = real_results.real_tests(sample(), n_perm=4_000)
    assert [r["test"] for r in rows] == list(TESTS)
    spearman = rows[1]
    assert 0 < spearman["p_permutation"] <= 1
    assert spearman["p_permutation"] == pytest.approx(spearman["p_value"], abs=0.02)


def test_real_tests_detect_no_association_under_independence():
    rows = real_results.real_tests(sample(seed=3, rho=0.0), n_perm=2_000)
    assert all(r["p_permutation"] > 0.05 for r in rows)


def test_calibration_interpolates_monotone_curve():
    curve = pd.Series({0.0: 0.0, 0.5: 0.3, 1.0: 0.8})
    assert real_results.calibrate_latent_rho(0.3, curve) == pytest.approx(0.5)
    assert real_results.calibrate_latent_rho(0.55, curve) == pytest.approx(0.75)


def test_required_n_returns_smallest_n_or_none():
    rows = []
    for ref, rates in {"observado": (0.5, 0.85, 0.95), "conservador": (0.1, 0.2, 0.3)}.items():
        for n, rate in zip((10, 20, 30), rates):
            for test in TESTS:
                rows.append({"reference": ref, "scenario": "realista", "label": "R", "n": n, "effect": 0.5,
                             "test": test, "rejections": 0, "n_sims": 100, "rate": rate,
                             "ci_low": rate, "ci_high": rate, "alpha": 0.05})
    curves = pd.DataFrame(rows)
    needed = real_results.required_n(curves)
    assert needed["observado"] == {"pearson": 20, "spearman": 20}
    assert needed["conservador"] == {"pearson": None, "spearman": None}


def test_committed_real_results_are_consistent():
    data = json.loads(real_results.REAL_RESULTS_PATH.read_text(encoding="utf-8"))
    assert data["n"] == 30 and {r["test"] for r in data["resultados"]} == set(TESTS)
    assert 0 < data["efeito_latente"]["conservador"] < data["efeito_latente"]["observado"] < 1
    curves = pd.read_csv(real_results.POWER_BY_N_PATH)
    assert set(curves.columns) == {"reference", *SIMULATION_COLUMNS}
    assert set(curves["n"]) == set(real_results.POWER_NS)
    real_n = curves[curves["n"] == 30]
    for ref, by_test in data["poder_no_n_real"].items():
        for test, rate in by_test.items():
            row = real_n[(real_n["reference"] == ref) & (real_n["test"] == test)]
            assert row["rate"].iloc[0] == pytest.approx(rate)


def test_power_by_n_figure():
    curves = pd.read_csv(real_results.POWER_BY_N_PATH)
    fig = poder_n.figure(curves, {"observado": "Obs", "conservador": "Cons"}, 30)
    assert len(fig.data) == 4
    assert fig.layout.xaxis.title.text == poder_n.X_TITLE
    assert sum(1 for t in fig.data if t.showlegend) == 2
    with pytest.raises(ValueError):
        poder_n.figure(curves, {"observado": "Obs"}, 30)
