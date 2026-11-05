import numpy as np
import pandas as pd
import pytest
from scipy import stats

from lab04.contracts import MarginalParams
from lab04.plots import g1_dados
from lab04.style import DATA_COLORS

PARAMS = MarginalParams(loc_mu=4.9, loc_sigma=1.5, defects_mean=0.75, defects_dispersion=0.25)


def _fixture(n, rho, seed):
    """Conjunto simulado de teste (cópula gaussiana), independente do gerador."""
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], size=n)
    loc = np.maximum(1, np.round(np.exp(PARAMS.loc_mu + PARAMS.loc_sigma * z[:, 0]))).astype(int)
    k, m = PARAMS.defects_dispersion, PARAMS.defects_mean
    defects = stats.nbinom.ppf(stats.norm.cdf(z[:, 1]), k, k / (k + m)).astype(int)
    return pd.DataFrame({"loc": loc, "defects": defects})


@pytest.fixture
def frames():
    return _fixture(30, 0.4, 1), _fixture(2000, 0.4, 2)


def test_figure_has_four_histograms(frames):
    fig = g1_dados.figure(*frames)
    assert len(fig.data) == 4
    assert all(t.type == "histogram" for t in fig.data)


def test_colors_follow_style_and_legend_is_not_duplicated(frames):
    fig = g1_dados.figure(*frames)
    colors = [t.marker.color for t in fig.data]
    real, sim = DATA_COLORS["real"], DATA_COLORS["simulado"]
    assert colors == [real, real, sim, sim]
    assert sum(1 for t in fig.data if t.showlegend is not False) == 2
    names = {t.name for t in fig.data if t.showlegend is not False}
    assert any("Real (n = 30)" in n for n in names)


def test_titles_axes_and_percent_scale(frames):
    fig = g1_dados.figure(*frames)
    assert fig.layout.title.text.startswith("G1")
    assert fig.layout.showlegend is True
    assert fig.layout.xaxis.title.text == g1_dados.X_TITLES["loc"]
    assert fig.layout.xaxis2.title.text == g1_dados.X_TITLES["defects"]
    assert fig.layout.yaxis.title.text == g1_dados.Y_TITLE
    assert fig.layout.yaxis.tickformat == ".0%"
    assert [a.text for a in fig.layout.annotations] == list(g1_dados.SUBPLOT_TITLES)


def test_real_and_simulated_are_side_by_side_with_same_bins(frames):
    fig = g1_dados.figure(*frames)
    assert fig.layout.barmode == "group"
    # Real (0, 1) e simulado (2, 3) no mesmo painel e com as mesmas faixas.
    assert fig.data[0].xaxis == fig.data[2].xaxis == "x"
    assert fig.data[1].xaxis == fig.data[3].xaxis == "x2"
    assert fig.data[0].xbins == fig.data[2].xbins
    assert fig.data[1].xbins == fig.data[3].xbins


def test_defects_tail_is_grouped(frames):
    real, sim = frames
    fig = g1_dados.figure(real.assign(defects=real["defects"] + 50), sim)
    assert max(fig.data[1].x) == g1_dados.DEFECTS_CAP
    assert fig.layout.xaxis2.ticktext[-1] == f"{g1_dados.DEFECTS_CAP}+"


def test_rejects_bad_input(frames):
    real, sim = frames
    with pytest.raises(ValueError):
        g1_dados.figure(real.drop(columns="defects"), sim)
    with pytest.raises(ValueError):
        g1_dados.figure(real, sim.iloc[0:0])
    with pytest.raises(ValueError):
        g1_dados.figure(real.assign(loc=0), sim)


def test_works_with_committed_real_sample():
    from lab04.config import SAMPLE_PATH

    real = pd.read_csv(SAMPLE_PATH)
    fig = g1_dados.figure(real, _fixture(500, 0.3, 3))
    assert len(fig.data) == 4
