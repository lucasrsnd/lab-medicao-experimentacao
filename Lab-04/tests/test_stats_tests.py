import numpy as np
import pytest
from scipy import stats

from lab04.contracts import TestResult
from lab04.stats_tests import pearson, pvalues, spearman


@pytest.mark.parametrize(
    ("function", "scipy_function", "test_name"),
    [
        (pearson, stats.pearsonr, "pearson"),
        (spearman, stats.spearmanr, "spearman"),
    ],
)
def test_results_match_scipy(function, scipy_function, test_name):
    rng = np.random.default_rng(42)
    x = rng.lognormal(2.0, 1.0, 200)
    y = rng.negative_binomial(2, 0.4, 200)
    result = function(x, y)
    expected = scipy_function(x, y)
    assert isinstance(result, TestResult)
    assert result.test == test_name
    assert result.effect == pytest.approx(expected.statistic, abs=1e-8)
    assert result.p_value == pytest.approx(expected.pvalue, abs=1e-8)
    assert result.statistic == pytest.approx(
        result.effect * np.sqrt((len(x) - 2) / (1 - result.effect**2)),
        abs=1e-8,
    )
    assert result.ci_low <= result.effect <= result.ci_high


def test_spearman_uses_average_ranks_for_ties():
    x = np.array([1, 1, 2, 3, 3, 3, 4, 5])
    y = np.array([2, 3, 1, 4, 4, 5, 6, 6])
    result = spearman(x, y)
    expected = stats.spearmanr(x, y)
    assert result.effect == pytest.approx(expected.statistic, abs=1e-8)
    assert result.p_value == pytest.approx(expected.pvalue, abs=1e-8)


@pytest.mark.parametrize(("test", "scipy_function"), [
    ("pearson", stats.pearsonr),
    ("spearman", stats.spearmanr),
])
def test_vectorized_pvalues_match_scipy(test, scipy_function):
    rng = np.random.default_rng(42)
    X = rng.normal(size=(20, 15))
    Y = rng.normal(size=(20, 15))
    if test == "spearman":
        X = np.round(X)
        Y = np.round(Y)
    actual = pvalues(test, X, Y)
    expected = np.array([scipy_function(x, y).pvalue for x, y in zip(X, Y)])
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0.0)


def test_pvalues_handles_ten_thousand_rows():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(10_000, 30))
    Y = rng.normal(size=(10_000, 30))
    values = pvalues("pearson", X, Y)
    assert values.shape == (10_000,)
    assert np.isfinite(values).all()
    assert ((values >= 0.0) & (values <= 1.0)).all()


def test_statistics_reject_invalid_inputs():
    with pytest.raises(ValueError):
        pearson(np.arange(4), np.ones(4))
    with pytest.raises(ValueError):
        spearman(np.arange(3), np.arange(3))
    with pytest.raises(ValueError):
        pvalues("kendall", np.ones((2, 5)), np.ones((2, 5)))
    with pytest.raises(ValueError):
        pvalues("pearson", np.ones((2, 5)), np.ones((3, 5)))
