import json

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from lab04 import real_data
from lab04.contracts import SAMPLE_COLUMNS, MarginalParams


def _synthetic(n, mu, sigma, mean, k, seed=1):
    rng = np.random.default_rng(seed)
    loc = np.round(rng.lognormal(mu, sigma, n)).clip(min=1).astype(int)
    p = k / (k + mean)
    defects = rng.negative_binomial(k, p, n)
    return pd.DataFrame({"module_id": [f"m{i}" for i in range(n)], "loc": loc, "defects": defects})


def test_fit_params_recovers_known_parameters():
    df = _synthetic(50_000, mu=5.0, sigma=1.2, mean=0.8, k=0.5)
    params = real_data.fit_params(df)
    assert isinstance(params, MarginalParams)
    assert params.loc_mu == pytest.approx(5.0, abs=0.05)
    assert params.loc_sigma == pytest.approx(1.2, abs=0.05)
    assert params.defects_mean == pytest.approx(0.8, abs=0.05)
    assert params.defects_dispersion == pytest.approx(0.5, rel=0.25)


def test_fit_params_without_overdispersion_caps_dispersion():
    df = pd.DataFrame({"loc": [10, 20, 30, 40], "defects": [1, 1, 1, 1]})  # variância 0 < média
    assert real_data.fit_params(df).defects_dispersion == real_data.MAX_DISPERSION


def test_fit_params_rejects_invalid_input():
    with pytest.raises(ValueError):
        real_data.fit_params(pd.DataFrame({"loc": [10, 20, 30], "defects": [0, 0, 0]}))
    with pytest.raises(ValueError):
        real_data.fit_params(pd.DataFrame({"loc": [0, 20, 30], "defects": [1, 0, 2]}))
    with pytest.raises(ValueError):
        real_data.fit_params(pd.DataFrame({"loc": [10, 20], "defects": [1, 2]}))


def test_observed_stats_match_scipy():
    df = _synthetic(500, 5.0, 1.0, 1.0, 1.0)
    obs = real_data.observed_stats(df)
    assert obs["pearson_r"] == pytest.approx(stats.pearsonr(df["loc"], df["defects"])[0])
    assert obs["spearman_rho"] == pytest.approx(stats.spearmanr(df["loc"], df["defects"])[0])
    assert obs["prop_zeros"] == pytest.approx((df["defects"] == 0).mean())


def test_draw_sample_is_reproducible_and_without_replacement():
    raw = _synthetic(200, 5.0, 1.0, 1.0, 1.0)
    a = real_data.draw_sample(raw, n=30, seed=42)
    b = real_data.draw_sample(raw, n=30, seed=42)
    assert a.equals(b)
    assert list(a.columns) == list(SAMPLE_COLUMNS)
    assert a["module_id"].is_unique and len(a) == 30
    with pytest.raises(ValueError):
        real_data.draw_sample(raw, n=500)


def test_load_sample_writes_csv(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    rows = ["name,version,name,loc,bug"] + [f"x,1,C{i},{10 + i},{i % 3}" for i in range(100)]
    rows.append("x,1,Empty,0,0")
    raw_csv.write_text("\n".join(rows), encoding="utf-8")
    out = tmp_path / "out" / "amostra.csv"
    sample = real_data.load_sample(raw_csv, out, n=30, seed=42)
    assert out.exists() and pd.read_csv(out).equals(sample)
    assert (sample["loc"] > 0).all()


def test_real_params_json_roundtrip(tmp_path):
    df = _synthetic(60, 5.0, 1.0, 1.0, 1.0)
    path = tmp_path / "real_params.json"
    content = real_data.write_real_params(df, path)
    assert json.loads(path.read_text(encoding="utf-8")) == content
    assert set(content) == {"fonte", "n", "params", "observado"}
    assert set(content["observado"]) == {
        "pearson_r", "spearman_rho", "assimetria_loc", "assimetria_defects", "prop_zeros",
    }
    params, observed = real_data.read_real_params(path)
    assert params == real_data.fit_params(df) and observed == content["observado"]


def test_committed_sample_matches_seed():
    sample = pd.read_csv(real_data.SAMPLE_PATH)
    assert len(sample) == 30 and list(sample.columns) == list(SAMPLE_COLUMNS)
    assert sample.equals(real_data.draw_sample(real_data.load_raw()))
