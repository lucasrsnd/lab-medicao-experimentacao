"""Estimativa Monte Carlo das taxas de rejeição dos testes de correlação."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS, Scenario
from lab04.simulation.generator import generate_batch
from lab04.stats_tests import pvalues


def _wilson_interval(rejections: int, n_sims: int) -> tuple[float, float]:
    """Calcula o intervalo de Wilson bilateral de 95% para uma proporção."""
    rate = rejections / n_sims
    z = 1.959963984540054
    denominator = 1.0 + z**2 / n_sims
    centre = (rate + z**2 / (2 * n_sims)) / denominator
    half_width = (
        z
        * np.sqrt(rate * (1.0 - rate) / n_sims + z**2 / (4 * n_sims**2))
        / denominator
    )
    return centre - half_width, centre + half_width


def rejection_rates(
    scenarios: list[Scenario],
    effects: tuple[float, ...],
    n_sims: int,
    alpha: float,
    seed: int,
) -> pd.DataFrame:
    """Calcula rejeições, taxas e ICs de 95% para cada cenário e efeito.

    Cada par cenário/efeito usa um lote vetorizado, e os dois testes são
    calculados sobre as mesmas amostras. A função não realiza operações de I/O.
    """
    if not scenarios:
        raise ValueError("É necessário fornecer ao menos um cenário.")
    if not effects:
        raise ValueError("É necessário fornecer ao menos um efeito.")
    if n_sims < 1:
        raise ValueError("n_sims deve ser positivo.")
    if not np.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha deve estar estritamente entre 0 e 1.")
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed deve ser um inteiro.")

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        for effect in effects:
            X, Y = generate_batch(scenario, effect, n_sims, rng)
            valid_rows = (np.ptp(X, axis=1) > 0) & (np.ptp(Y, axis=1) > 0)
            for test in TESTS:
                p_values = np.ones(n_sims, dtype=float)
                if valid_rows.any():
                    p_values[valid_rows] = pvalues(
                        test,
                        X[valid_rows],
                        Y[valid_rows],
                    )
                rejections = int(np.count_nonzero(p_values < alpha))
                rate = rejections / n_sims
                ci_low, ci_high = _wilson_interval(rejections, n_sims)
                rows.append(
                    {
                        "scenario": scenario.name,
                        "label": scenario.label,
                        "n": scenario.n,
                        "effect": effect,
                        "test": test,
                        "rejections": rejections,
                        "n_sims": n_sims,
                        "rate": rate,
                        "ci_low": ci_low,
                        "ci_high": ci_high,
                        "alpha": alpha,
                    }
                )
    return pd.DataFrame(rows, columns=SIMULATION_COLUMNS)
