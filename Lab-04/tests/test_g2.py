import numpy as np
import pytest
from scipy import stats

from lab04.permutation import permutation_null
from lab04.plots import g2_nula
from lab04.style import TEST_COLORS

N = 30


def synthetic_pair(seed=0, rho=0.4):
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal((0, 0), ((1, rho), (rho, 1)), size=N)
    return np.exp(z[:, 0]), np.floor(np.exp(z[:, 1]))


def t_from_r(r, n=N):
    return r * np.sqrt((n - 2) / (1 - r**2))


def area(trace):
    return float(np.trapezoid(trace.y, trace.x))


def traces_named(fig, prefix):
    return [t for t in fig.data if (t.legendgroup or "") == prefix]


def test_p_value_matches_scipy():
    x, y = synthetic_pair()
    r, p = stats.pearsonr(x, y)
    assert g2_nula.p_value(N, t_from_r(r)) == pytest.approx(p, rel=1e-9)
    rho, p_s = stats.spearmanr(x, y)
    assert g2_nula.p_value(N, t_from_r(rho)) == pytest.approx(p_s, rel=1e-9)


@pytest.mark.parametrize("test", ["pearson", "spearman"])
def test_shaded_areas_equal_p_value_and_alpha(test):
    t_obs = 2.6
    fig = g2_nula.figure(test, N, t_obs)
    p_area = sum(area(t) for t in traces_named(fig, "pvalor"))
    rejection_area = sum(area(t) for t in traces_named(fig, "rejeicao"))
    assert p_area == pytest.approx(g2_nula.p_value(N, t_obs), abs=1e-3)
    assert rejection_area == pytest.approx(0.05, abs=1e-3)


def test_rejection_region_starts_at_critical_value():
    fig = g2_nula.figure("pearson", N, 1.0)
    crit = stats.t.ppf(0.975, N - 2)
    left, right = traces_named(fig, "rejeicao")
    assert left.x.max() == pytest.approx(-crit)
    assert right.x.min() == pytest.approx(crit)


def test_negative_statistic_shades_both_tails():
    fig = g2_nula.figure("spearman", N, -2.3)
    left, right = traces_named(fig, "pvalor")
    assert left.x.max() == pytest.approx(-2.3) and right.x.min() == pytest.approx(2.3)


def test_uses_test_color_and_has_title_axes_legend():
    fig = g2_nula.figure("spearman", N, 2.0)
    assert all(t.fillcolor == TEST_COLORS["spearman"] for t in traces_named(fig, "pvalor"))
    assert "Spearman" in fig.layout.title.text
    assert fig.layout.xaxis.title.text and fig.layout.yaxis.title.text
    assert fig.layout.showlegend is True


def test_permutation_null_is_reproducible_and_centered():
    x, y = synthetic_pair(seed=1, rho=0.0)
    a = permutation_null("spearman", x, y, n_perm=4_000, rng=np.random.default_rng(7))
    b = permutation_null("spearman", x, y, n_perm=4_000, rng=np.random.default_rng(7))
    np.testing.assert_array_equal(a, b)
    assert abs(a.mean()) < 0.1
    # Para postos sem empates a nula por permutação é próxima da t(n−2).
    assert a.std() == pytest.approx(stats.t.std(N - 2), rel=0.1)


def test_permutation_overlay_is_drawn():
    x, y = synthetic_pair()
    nulls = permutation_null("pearson", x, y, n_perm=500)
    fig = g2_nula.figure("pearson", N, 2.0, null_statistics=nulls)
    assert any("permutação" in (t.name or "") for t in fig.data)


@pytest.mark.parametrize("kwargs", [{"test": "kendall"}, {"n": 3}, {"alpha": 0.0}])
def test_invalid_arguments(kwargs):
    args = {"test": "pearson", "n": N, "observed_statistic": 1.0, **kwargs}
    with pytest.raises(ValueError):
        g2_nula.figure(**args)
