"""Geração de amostras marginais com uma cópula gaussiana."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from lab04.contracts import MarginalParams, Scenario


def _validate_dimensions(n: int, rho: float) -> None:
    if n < 1:
        raise ValueError("n deve ser positivo.")
    if not np.isfinite(rho) or not -1.0 <= rho <= 1.0:
        raise ValueError("rho deve ser finito e estar em [-1, 1].")


def _draw(
    params: MarginalParams,
    n: int,
    rho: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    _validate_dimensions(n, rho)
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng deve ser uma instância de numpy.random.Generator.")

    latent = rng.multivariate_normal(
        mean=(0.0, 0.0),
        cov=((1.0, rho), (rho, 1.0)),
        size=n,
    )
    loc = np.rint(np.exp(params.loc_mu + params.loc_sigma * latent[:, 0]))

    probability = stats.norm.cdf(latent[:, 1])
    probability = np.clip(probability, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
    mean = params.defects_mean
    dispersion = params.defects_dispersion
    defects = stats.nbinom.ppf(
        probability,
        dispersion,
        dispersion / (dispersion + mean),
    )
    return np.maximum(loc, 1.0).astype(np.int64), defects.astype(np.int64)


def generate(
    params: MarginalParams,
    n: int,
    rho: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Gera LOC e defeitos para ``n`` observações usando a cópula gaussiana."""
    loc, defects = _draw(params, n, rho, rng)
    return pd.DataFrame({"loc": loc, "defects": defects})


def generate_batch(
    scenario: Scenario,
    rho: float,
    n_sims: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Gera ``n_sims`` amostras vetorizadas, cada uma com ``scenario.n`` itens."""
    _validate_dimensions(scenario.n, rho)
    if n_sims < 1:
        raise ValueError("n_sims deve ser positivo.")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng deve ser uma instância de numpy.random.Generator.")

    latent = rng.multivariate_normal(
        mean=(0.0, 0.0),
        cov=((1.0, rho), (rho, 1.0)),
        size=(n_sims, scenario.n),
    )
    loc = np.maximum(
        np.rint(np.exp(scenario.params.loc_mu + scenario.params.loc_sigma * latent[..., 0])),
        1.0,
    ).astype(np.int64)

    probability = stats.norm.cdf(latent[..., 1])
    probability = np.clip(probability, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
    mean = scenario.params.defects_mean
    dispersion = scenario.params.defects_dispersion
    defects = stats.nbinom.ppf(
        probability,
        dispersion,
        dispersion / (dispersion + mean),
    ).astype(np.int64)

    if scenario.postprocess is not None:
        loc, defects = scenario.postprocess(loc, defects, rng)
        loc = np.asarray(loc)
        defects = np.asarray(defects)
        expected_shape = (n_sims, scenario.n)
        if loc.shape != expected_shape or defects.shape != expected_shape:
            raise ValueError(f"postprocess deve preservar o formato {expected_shape}.")
    return loc, defects
