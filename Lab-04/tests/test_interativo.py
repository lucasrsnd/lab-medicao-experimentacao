import pytest

from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS
from lab04.dashboard import interativo


def test_scenarios_offered_exclude_fixed_small_sample():
    names = [s.name for s in interativo.interactive_scenarios()]
    assert names[0] == "realista"
    assert {"outliers", "assimetria_extrema"} <= set(names)
    assert "amostra_pequena" not in names


def test_simulate_returns_full_curve_for_chosen_n():
    results = interativo.simulate("realista", 40, n_sims=200)
    assert list(results.columns) == list(SIMULATION_COLUMNS)
    assert set(results["n"]) == {40}
    assert sorted(results["effect"].unique()) == list(interativo.EFFECT_GRID)
    assert set(results["test"]) == set(TESTS)


def test_simulate_is_reproducible():
    a = interativo.simulate("outliers", 20, n_sims=200)
    b = interativo.simulate("outliers", 20, n_sims=200)
    assert a.equals(b)


def test_power_grows_with_sample_size():
    small = interativo.at_effect(interativo.simulate("realista", 10, n_sims=400), 0.5)
    large = interativo.at_effect(interativo.simulate("realista", 120, n_sims=400), 0.5)
    for test in TESTS:
        assert large[test]["rate"] > small[test]["rate"]


@pytest.mark.parametrize("n", [5, 151])
def test_rejects_n_outside_slider_range(n):
    with pytest.raises(ValueError):
        interativo.simulate("realista", n)
