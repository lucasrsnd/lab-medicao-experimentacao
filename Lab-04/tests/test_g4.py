import itertools

import pandas as pd
import pytest

from lab04.config import SIMULATIONS_PATH
from lab04.contracts import SIMULATION_COLUMNS
from lab04.plots import g4_poder
from lab04.style import TEST_COLORS

EFFECTS = (0.0, 0.2, 0.4)


def frame(scenarios=(("realista", "Realista", 30), ("pequena", "Amostra pequena (n = 10)", 10))):
    rows = []
    for (name, label, n), effect, test in itertools.product(scenarios, EFFECTS, ("pearson", "spearman")):
        rate = 0.05 + effect * (0.9 if test == "spearman" else 0.7)
        rows.append({
            "scenario": name, "label": label, "n": n, "effect": effect, "test": test,
            "rejections": int(rate * 1000), "n_sims": 1000, "rate": rate,
            "ci_low": rate - 0.01, "ci_high": rate + 0.01, "alpha": 0.05,
        })
    return pd.DataFrame(rows, columns=SIMULATION_COLUMNS)


def test_one_panel_per_scenario_with_both_tests():
    fig = g4_poder.figure(frame())
    assert len(fig.data) == 4
    assert [a.text for a in fig.layout.annotations][:2] == ["Realista<br>n = 30", "Amostra pequena (n = 10)"]
    assert {t.xaxis for t in fig.data} == {"x", "x2"}


def test_colors_dash_and_single_legend_per_test():
    fig = g4_poder.figure(frame())
    for trace in fig.data:
        test = trace.legendgroup
        assert trace.line.color == TEST_COLORS[test]
        assert trace.line.dash == g4_poder.DASH[test]
    assert sum(1 for t in fig.data if t.showlegend) == 2


def test_rates_in_percent_with_ci_and_80_percent_reference():
    fig = g4_poder.figure(frame())
    spearman = fig.data[1]
    assert list(spearman.y) == pytest.approx([5.0, 23.0, 41.0])
    assert all(v == pytest.approx(1.0) for v in spearman.error_y.array)
    assert sum(1 for s in fig.layout.shapes if s.y0 == 80) == 2
    assert fig.layout.yaxis.range == (0, 100)


def test_title_axes_and_legend():
    fig = g4_poder.figure(frame(), title="Outro título")
    assert fig.layout.title.text == "Outro título"
    assert fig.layout.xaxis.title.text == g4_poder.X_TITLE
    assert fig.layout.yaxis.title.text == g4_poder.Y_TITLE
    assert fig.layout.showlegend is True


@pytest.mark.parametrize("broken", [
    lambda d: d.drop(columns="rate"),
    lambda d: pd.concat([d, d.head(1)]),
    lambda d: d.assign(test="kendall"),
    lambda d: d[d["effect"] == 0],
    lambda d: d.iloc[0:0],
])
def test_rejects_bad_input(broken):
    with pytest.raises(ValueError):
        g4_poder.figure(broken(frame()))


def test_works_with_committed_simulations():
    results = pd.read_csv(SIMULATIONS_PATH)
    fig = g4_poder.figure(results)
    assert len(fig.data) == 2 * results["scenario"].nunique()
