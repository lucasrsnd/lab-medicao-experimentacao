import numpy as np
import pandas as pd
import pytest

from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS, MarginalParams, Scenario
from lab04.simulation.montecarlo import rejection_rates

NORMAL_LIKE = MarginalParams(
    loc_mu=4.5,
    loc_sigma=0.15,
    defects_mean=30.0,
    defects_dispersion=100_000.0,
)
SCENARIO = Scenario("normal_like", "Marginais aproximadamente normais", 60, NORMAL_LIKE)


def test_output_columns_and_type_i_rate_for_uncorrelated_marginals():
    results = rejection_rates([SCENARIO], (0.0,), 5_000, 0.05, 42)

    assert list(results.columns) == list(SIMULATION_COLUMNS)
    assert set(results["test"]) == set(TESTS)
    assert (results["rate"] - 0.05).abs().max() < 0.02
    assert (results["ci_low"] <= results["rate"]).all()
    assert (results["rate"] <= results["ci_high"]).all()


def test_power_increases_with_effect():
    results = rejection_rates([SCENARIO], (0.0, 0.3, 0.6), 3_000, 0.05, 42)
    for _, test_results in results.groupby("test"):
        rates = test_results.sort_values("effect")["rate"].to_numpy()
        assert np.all(np.diff(rates) > 0)


def test_fixed_seed_returns_identical_dataframe():
    first = rejection_rates([SCENARIO], (0.0, 0.2, 0.4), 500, 0.05, 42)
    second = rejection_rates([SCENARIO], (0.0, 0.2, 0.4), 500, 0.05, 42)
    pd.testing.assert_frame_equal(first, second)


def test_constant_samples_are_counted_as_non_rejections(monkeypatch):
    X = np.tile(np.arange(SCENARIO.n), (3, 1))
    Y = np.tile(np.arange(SCENARIO.n), (3, 1))
    X[0] = 1
    Y[1] = 1

    def generate_with_constant_rows(scenario, effect, n_sims, rng):
        return X, Y

    monkeypatch.setattr(
        "lab04.simulation.montecarlo.generate_batch",
        generate_with_constant_rows,
    )
    results = rejection_rates([SCENARIO], (0.0,), 3, 0.05, 42)

    assert (results["rejections"] <= 1).all()


@pytest.mark.parametrize(
    ("effects", "n_sims", "alpha"),
    [((), 100, 0.05), ((0.0,), 0, 0.05), ((0.0,), 100, 1.0)],
)
def test_invalid_simulation_configuration_is_rejected(effects, n_sims, alpha):
    with pytest.raises(ValueError):
        rejection_rates([SCENARIO], effects, n_sims, alpha, 42)
