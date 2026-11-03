import numpy as np
import pytest
from scipy import stats

from lab04.contracts import MarginalParams, Scenario
from lab04.simulation.generator import generate, generate_batch
from lab04.simulation.scenarios import all_scenarios, get, register

PARAMS = MarginalParams(
    loc_mu=4.9,
    loc_sigma=1.5,
    defects_mean=0.75,
    defects_dispersion=0.25,
)


def test_generate_is_reproducible_with_same_seed():
    first = generate(PARAMS, 100, 0.4, np.random.default_rng(42))
    second = generate(PARAMS, 100, 0.4, np.random.default_rng(42))
    assert first.equals(second)
    assert list(first.columns) == ["loc", "defects"]


def test_rho_zero_produces_independent_marginals():
    sample = generate(PARAMS, 20_000, 0.0, np.random.default_rng(42))
    correlation, _ = stats.spearmanr(sample["loc"], sample["defects"])
    assert abs(correlation) < 0.03


def test_marginal_mean_and_median_match_parameters():
    sample = generate(PARAMS, 100_000, 0.0, np.random.default_rng(42))
    expected_loc_mean = np.exp(PARAMS.loc_mu + PARAMS.loc_sigma**2 / 2)
    assert sample["loc"].median() == pytest.approx(np.exp(PARAMS.loc_mu), rel=0.01)
    assert sample["loc"].mean() == pytest.approx(expected_loc_mean, rel=0.02)
    assert sample["defects"].mean() == pytest.approx(PARAMS.defects_mean, abs=0.025)


def test_spearman_correlation_increases_with_latent_rho():
    correlations = []
    for rho in (0.0, 0.3, 0.7):
        loc, defects = generate_batch(
            Scenario("test", "Teste", 2_000, PARAMS),
            rho,
            1,
            np.random.default_rng(100),
        )
        correlations.append(stats.spearmanr(loc[0], defects[0]).statistic)
    assert correlations[0] < correlations[1] < correlations[2]


def test_generate_batch_shape_and_postprocess():
    def postprocess(loc, defects, rng):
        return loc + 1, defects

    scenario = Scenario("post", "Pós-processado", 12, PARAMS, postprocess)
    loc, defects = generate_batch(scenario, 0.2, 5, np.random.default_rng(42))
    assert loc.shape == defects.shape == (5, 12)
    without_postprocess, _ = generate_batch(
        Scenario("raw", "Bruto", 12, PARAMS),
        0.2,
        5,
        np.random.default_rng(42),
    )
    np.testing.assert_array_equal(loc, without_postprocess + 1)


def test_generator_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        generate(PARAMS, 0, 0.0, np.random.default_rng(42))
    with pytest.raises(ValueError):
        generate(PARAMS, 10, 1.1, np.random.default_rng(42))
    with pytest.raises(ValueError):
        generate_batch(Scenario("test", "Teste", 4, PARAMS), 0.0, 0, np.random.default_rng(42))


def test_scenario_registry_supports_register_get_and_list():
    scenario = Scenario("unitario", "Unitário", 10, PARAMS)
    register(scenario)
    assert get("unitario") is scenario
    assert scenario in all_scenarios()
    assert get("realista").n == 30
    with pytest.raises(ValueError):
        register(scenario)
    with pytest.raises(KeyError):
        get("inexistente")
