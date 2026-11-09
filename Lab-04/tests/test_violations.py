import numpy as np
import pytest
from scipy import stats

from lab04.config import SEED
from lab04.simulation import violations
from lab04.simulation.generator import generate_batch
from lab04.simulation.scenarios import all_scenarios, get
from lab04.simulation.violations import (
    DEFECTS_OUTLIER_SHIFT, LOC_OUTLIER_FACTOR, OUTLIER_FRACTION, build_violations,
    inject_outliers, register_violations,
)

BASE = get("realista").params
SHAPE = (4_000, 30)


def base_batch(seed=SEED, rho=0.0):
    return generate_batch(get("realista"), rho, SHAPE[0], np.random.default_rng(seed))


def test_registers_at_least_two_scenarios_and_is_idempotent():
    first = register_violations()
    second = register_violations()
    assert len(first) >= 2
    assert [s.name for s in first] == [s.name for s in second]
    names = [s.name for s in all_scenarios()]
    assert len(names) == len(set(names))
    assert {"outliers", "assimetria_extrema", "amostra_pequena"} <= set(names)


def test_violation_scenarios_only_use_postprocess_and_parameters():
    by_name = {s.name: s for s in build_violations(BASE)}
    assert by_name["outliers"].postprocess is inject_outliers
    assert by_name["amostra_pequena"].n == violations.SMALL_SAMPLE_N == 10
    # A assimetria extrema muda só as marginais.
    skew = by_name["assimetria_extrema"]
    assert skew.postprocess is None
    assert skew.params.loc_sigma > BASE.loc_sigma
    assert skew.params.defects_dispersion < BASE.defects_dispersion
    assert skew.params.defects_mean == BASE.defects_mean


def test_outlier_fraction_is_as_documented():
    loc, defects = base_batch()
    new_loc, new_defects = inject_outliers(loc, defects, np.random.default_rng(1))
    loc_changed = new_loc != loc
    defects_changed = new_defects != defects
    # 120 mil observações: o desvio-padrão da fração é ~0,0006.
    assert loc_changed.mean() == pytest.approx(OUTLIER_FRACTION, abs=0.003)
    assert defects_changed.mean() == pytest.approx(OUTLIER_FRACTION, abs=0.003)
    np.testing.assert_array_equal(new_loc[loc_changed], loc[loc_changed] * LOC_OUTLIER_FACTOR)
    np.testing.assert_array_equal(
        new_defects[defects_changed], defects[defects_changed] + DEFECTS_OUTLIER_SHIFT
    )


def test_outliers_are_injected_independently_in_x_and_y():
    loc, defects = base_batch()
    new_loc, new_defects = inject_outliers(loc, defects, np.random.default_rng(2))
    both = ((new_loc != loc) & (new_defects != defects)).mean()
    # Máscaras independentes: P(ambos) = f².
    assert both == pytest.approx(OUTLIER_FRACTION**2, abs=0.001)


def test_h0_still_true_with_rho_zero():
    scenario = next(s for s in build_violations(BASE) if s.name == "outliers")
    loc, defects = generate_batch(scenario, 0.0, SHAPE[0], np.random.default_rng(SEED))
    assert loc.shape == defects.shape == (SHAPE[0], scenario.n)
    # A correlação de postos por amostra é centrada em zero (sem associação induzida).
    rho_s = [stats.spearmanr(l, d).statistic for l, d in zip(loc[:1_000], defects[:1_000])]
    assert np.nanmean(rho_s) == pytest.approx(0.0, abs=0.02)
    # Ter outlier em X não muda a chance de ter outlier em Y.
    plain = generate_batch(
        get("realista"), 0.0, SHAPE[0], np.random.default_rng(SEED)
    )
    x_out, y_out = loc != plain[0], defects != plain[1]
    assert y_out[x_out].mean() == pytest.approx(y_out[~x_out].mean(), abs=0.01)


def test_outliers_are_reproducible_and_keep_shape_and_integer_type():
    loc, defects = base_batch()
    a = inject_outliers(loc, defects, np.random.default_rng(3))
    b = inject_outliers(loc, defects, np.random.default_rng(3))
    np.testing.assert_array_equal(a[0], b[0])
    np.testing.assert_array_equal(a[1], b[1])
    assert a[0].shape == loc.shape and a[1].shape == defects.shape
    assert np.issubdtype(a[0].dtype, np.integer) and np.issubdtype(a[1].dtype, np.integer)


def test_extreme_skew_is_more_skewed_than_realistic():
    realistic = base_batch()
    skewed = generate_batch(
        next(s for s in build_violations(BASE) if s.name == "assimetria_extrema"),
        0.0, SHAPE[0], np.random.default_rng(SEED),
    )
    for variable in (0, 1):
        assert stats.skew(skewed[variable].ravel()) > stats.skew(realistic[variable].ravel())
