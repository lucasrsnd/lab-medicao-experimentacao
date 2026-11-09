import numpy as np
import pandas as pd
import pytest

from lab04.contracts import SIMULATION_COLUMNS
from lab04.plots import g3_erro_tipo1
from lab04.style import TEST_COLORS, TEST_LABELS

N_SIMS = 10_000
# (cenário, rótulo, n, taxa Pearson, taxa Spearman) com efeito 0.
TYPE1 = (
    ("realista", "Realista", 30, 0.0510, 0.0498),
    ("outliers", "Outliers", 30, 0.0820, 0.0505),
    ("amostra_pequena", "Amostra pequena", 10, 0.0300, 0.0490),
)


def wilson(rate, n=N_SIMS, z=1.96):
    centre = (rate + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


def synthetic(with_power=True) -> pd.DataFrame:
    rows = []
    for scenario, label, n, *rates in TYPE1:
        for test, rate in zip(("pearson", "spearman"), rates):
            low, high = wilson(rate)
            rows.append((scenario, label, n, 0.0, test, round(rate * N_SIMS), N_SIMS, rate, low, high, 0.05))
            if with_power:
                rows.append((scenario, label, n, 0.3, test, 5_000, N_SIMS, 0.5, 0.49, 0.51, 0.05))
    return pd.DataFrame(rows, columns=SIMULATION_COLUMNS)


def test_only_effect_zero_rows_are_plotted_in_percent():
    fig = g3_erro_tipo1.figure(synthetic())
    assert len(fig.data) == 2
    pearson = next(t for t in fig.data if t.name == TEST_LABELS["pearson"])
    assert list(pearson.y) == pytest.approx([5.10, 8.20, 3.00])


def test_confidence_interval_bars_and_reference_line():
    fig = g3_erro_tipo1.figure(synthetic())
    pearson = next(t for t in fig.data if t.name == TEST_LABELS["pearson"])
    low, high = wilson(0.0820)
    assert pearson.error_y.array[1] == pytest.approx(high * 100 - 8.20)
    assert pearson.error_y.arrayminus[1] == pytest.approx(8.20 - low * 100)
    lines = [s for s in fig.layout.shapes if s.type == "line"]
    assert len(lines) == 1 and lines[0].y0 == lines[0].y1 == pytest.approx(5.0)
    assert "5%" in fig.layout.annotations[0].text


def test_title_axes_legend_and_colors():
    fig = g3_erro_tipo1.figure(synthetic())
    assert "Erro tipo I" in fig.layout.title.text
    assert "%" in fig.layout.yaxis.title.text and fig.layout.xaxis.title.text
    assert fig.layout.showlegend is True
    for test in ("pearson", "spearman"):
        trace = next(t for t in fig.data if t.name == TEST_LABELS[test])
        assert trace.marker.color == TEST_COLORS[test]


def test_scenarios_keep_file_order_and_show_n():
    fig = g3_erro_tipo1.figure(synthetic())
    assert [c.split("<br>")[0] for c in fig.data[0].x] == ["Realista", "Outliers", "Amostra pequena"]
    assert fig.data[0].x[2].endswith("n = 10")


def test_classify_liberal_conservative_and_close():
    verdicts = g3_erro_tipo1.classify(synthetic()).set_index(["scenario", "test"])["verdict"]
    assert verdicts["realista", "pearson"] == g3_erro_tipo1.CLOSE
    assert verdicts["realista", "spearman"] == g3_erro_tipo1.CLOSE
    assert verdicts["outliers", "pearson"] == g3_erro_tipo1.LIBERAL
    assert verdicts["outliers", "spearman"] == g3_erro_tipo1.CLOSE
    assert verdicts["amostra_pequena", "pearson"] == g3_erro_tipo1.CONSERVATIVE


def test_invalid_results_are_rejected():
    good = synthetic()
    with pytest.raises(ValueError, match="colunas"):
        g3_erro_tipo1.figure(good.drop(columns=["ci_low"]))
    with pytest.raises(ValueError, match="effect == 0"):
        g3_erro_tipo1.figure(good[good["effect"] > 0])
    with pytest.raises(ValueError, match="mais de uma linha"):
        g3_erro_tipo1.figure(pd.concat([good, good[good["effect"] == 0]]))


def test_section4_text_has_expected_blocks():
    from lab04.dashboard import content

    assert {"O que observar", "Conclusão"} <= set(content.section_parts("04-erro-tipo1"))
