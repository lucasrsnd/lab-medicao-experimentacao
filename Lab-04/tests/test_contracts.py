from dataclasses import FrozenInstanceError

import plotly.graph_objects as go
import pytest

from lab04 import config
from lab04.contracts import MarginalParams, Scenario, TestResult
from lab04.style import TEST_COLORS, TEST_LABELS, apply_layout

PARAMS = MarginalParams(loc_mu=4.5, loc_sigma=1.0, defects_mean=1.2, defects_dispersion=0.8)


def result(**overrides):
    values = dict(test="pearson", statistic=2.1, p_value=0.04, effect=0.37,
                  ci_low=0.02, ci_high=0.64, n=30)
    return TestResult(**{**values, **overrides})


def test_config_follows_statement():
    assert config.SEED == 42
    assert config.ALPHA == 0.05
    assert config.N_SIMS == 10_000
    assert len(config.EFFECTS) >= 5 and config.EFFECTS[0] == 0
    assert list(config.EFFECTS) == sorted(config.EFFECTS)
    assert config.TESTS == ("pearson", "spearman")
    assert config.OUTPUTS_DIR.parent == config.LAB_ROOT


def test_marginal_params_roundtrip_and_validation():
    assert MarginalParams.from_dict(PARAMS.to_dict()) == PARAMS
    with pytest.raises(ValueError):
        MarginalParams(loc_mu=4.5, loc_sigma=0.0, defects_mean=1.2, defects_dispersion=0.8)
    with pytest.raises(ValueError):
        MarginalParams(loc_mu=float("nan"), loc_sigma=1, defects_mean=1, defects_dispersion=1)


def test_contracts_are_immutable():
    with pytest.raises(FrozenInstanceError):
        PARAMS.loc_mu = 0.0


def test_scenario_validation():
    scenario = Scenario(name="realista", label="Realista", n=30, params=PARAMS)
    assert scenario.postprocess is None
    with pytest.raises(ValueError):
        Scenario(name="com espaço", label="x", n=30, params=PARAMS)
    with pytest.raises(ValueError):
        Scenario(name="pequena", label="x", n=3, params=PARAMS)


def test_test_result_roundtrip_and_validation():
    assert TestResult.from_dict(result().to_dict()) == result()
    with pytest.raises(ValueError):
        result(test="kendall")
    with pytest.raises(ValueError):
        result(p_value=1.5)
    with pytest.raises(ValueError):
        result(ci_low=0.5)  # IC não contém a estimativa


def test_every_test_has_color_and_label():
    assert set(TEST_COLORS) == set(TEST_LABELS) == set(config.TESTS)
    assert len(set(TEST_COLORS.values())) == len(TEST_COLORS)


def test_apply_layout_sets_title_axes_and_legend():
    fig = apply_layout(go.Figure(), "Título", "LOC (linhas)", "Frequência (módulos)")
    assert fig.layout.title.text == "Título"
    assert fig.layout.xaxis.title.text == "LOC (linhas)"
    assert fig.layout.yaxis.title.text == "Frequência (módulos)"
    assert fig.layout.showlegend is True
    with pytest.raises(ValueError):
        apply_layout(go.Figure(), "", "x", "y")
