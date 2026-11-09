import json

import numpy as np
import pandas as pd
import pytest

from lab04.config import REAL_PARAMS_PATH
from lab04.contracts import MarginalParams, Scenario
from lab04.simulation.sample_size import (
    minimum_sample_sizes,
    power_at_observed_n,
    power_by_n,
)

SCENARIO = Scenario(
    "sample_size_test",
    "Teste de tamanho amostral",
    20,
    MarginalParams(4.5, 0.15, 30.0, 100_000.0),
)


@pytest.fixture
def real_params():
    with REAL_PARAMS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_power_increases_with_sample_size():
    results = power_by_n(SCENARIO, 0.5, [20, 40, 60], n_sims=2_000)
    for _, test_results in results.groupby("test"):
        rates = test_results.sort_values("n")["rate"].to_numpy()
        assert np.all(np.diff(rates) > 0)


def test_power_by_n_is_reproducible():
    first = power_by_n(SCENARIO, 0.4, [20, 35], n_sims=300)
    second = power_by_n(SCENARIO, 0.4, [20, 35], n_sims=300)
    pd.testing.assert_frame_equal(first, second)


def test_observed_power_and_minimum_sample_sizes_from_real_params(real_params):
    observed_effect = real_params["observado"]["spearman_rho"]

    observed_power = power_at_observed_n(SCENARIO, observed_effect, n_sims=200)
    assert set(observed_power["n"]) == {SCENARIO.n}
    assert set(observed_power["effect"]) == {observed_effect}

    results = power_by_n(SCENARIO, observed_effect, [20, 40, 60], n_sims=2_000)
    minimums = minimum_sample_sizes(results)
    assert list(minimums["test"]) == ["pearson", "spearman"]
    assert (minimums["target_power"] == 0.8).all()


def test_invalid_sample_sizes_are_rejected():
    with pytest.raises(ValueError):
        power_by_n(SCENARIO, 0.3, [])
    with pytest.raises(ValueError):
        power_by_n(SCENARIO, 0.3, [20, 20])
    with pytest.raises(ValueError):
        power_by_n(SCENARIO, 0.3, [3])


def test_minimum_sample_sizes_requires_simulation_columns():
    with pytest.raises(ValueError, match="colunas"):
        minimum_sample_sizes(pd.DataFrame())
