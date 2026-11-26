"""Poder × tamanho da amostra por Monte Carlo, com parâmetros estimados do piloto.

Reaproveita a abordagem do Lab04: gerar muitos conjuntos sob um modelo ajustado aos dados,
aplicar o teste a cada um e contar as rejeições. Aqui as duas condições são modeladas como
lognormais (tempos e tamanhos são positivos e assimétricos) ou normais. No desenho pareado,
a correlação ``rho`` entre as medidas da mesma unidade entra por uma cópula gaussiana.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from analise.config import ALPHA, N_SIMS, PODER_ALVO, SEED
from analise.descritiva import validate

DISTRIBUICOES = ("lognormal", "normal")


@dataclass(frozen=True)
class GroupParams:
    dist: str
    loc: float    # média (normal) ou média do log (lognormal)
    scale: float  # desvio (normal) ou desvio do log (lognormal)


def fit(values: np.ndarray, dist: str = "lognormal") -> GroupParams:
    """Ajusta os parâmetros de um grupo a partir dos valores do piloto."""
    if dist not in DISTRIBUICOES:
        raise ValueError(f"dist deve ser uma de {DISTRIBUICOES}.")
    data = np.asarray(values, dtype=float)
    if data.size < 3:
        raise ValueError("São necessárias ao menos 3 observações para ajustar parâmetros.")
    if dist == "lognormal":
        if (data <= 0).any():
            raise ValueError("Lognormal exige valores positivos; use dist='normal'.")
        data = np.log(data)
    return GroupParams(dist, float(data.mean()), float(data.std(ddof=1)))


def params_from_pilot(
    df: pd.DataFrame, metrica: str, tratamento_a: str, tratamento_b: str, dist: str = "lognormal"
) -> tuple[GroupParams, GroupParams]:
    data = validate(df)
    data = data[data["metrica"] == metrica]
    values = [data.loc[data["tratamento"] == t, "valor"].to_numpy() for t in (tratamento_a, tratamento_b)]
    return fit(values[0], dist), fit(values[1], dist)


def _transform(z: np.ndarray, params: GroupParams) -> np.ndarray:
    values = params.loc + params.scale * z
    return np.exp(values) if params.dist == "lognormal" else values


def _draw(a: GroupParams, b: GroupParams, n: int, n_sims: int, rho: float, rng: np.random.Generator):
    latent = rng.multivariate_normal((0.0, 0.0), ((1.0, rho), (rho, 1.0)), size=(n_sims, n))
    return _transform(latent[..., 0], a), _transform(latent[..., 1], b)


def _pvalues(x: np.ndarray, y: np.ndarray, pareado: bool) -> dict[str, np.ndarray]:
    if pareado:
        return {
            "t pareado": stats.ttest_rel(x, y, axis=1).pvalue,
            "Wilcoxon": stats.wilcoxon(x, y, axis=1).pvalue,
        }
    return {
        "t de Welch": stats.ttest_ind(x, y, equal_var=False, axis=1).pvalue,
        "Mann-Whitney U": stats.mannwhitneyu(x, y, alternative="two-sided", axis=1).pvalue,
    }


def power_by_n(
    a: GroupParams,
    b: GroupParams,
    ns: list[int],
    pareado: bool = False,
    rho: float = 0.0,
    n_sims: int = N_SIMS,
    alpha: float = ALPHA,
    seed: int = SEED,
) -> pd.DataFrame:
    """Proporção de rejeições de H0 para cada n (observações por grupo) e teste.

    O IC 95% é o de Monte Carlo (Wilson) da proporção estimada.
    """
    if not -1.0 < rho < 1.0:
        raise ValueError("rho deve estar em (-1, 1).")
    if not pareado and rho != 0.0:
        raise ValueError("rho só se aplica ao desenho pareado.")
    if min(ns) < 3:
        raise ValueError("Cada n deve ser ao menos 3.")
    rng = np.random.default_rng(seed)
    z = stats.norm.ppf(0.975)
    rows = []
    for n in ns:
        x, y = _draw(a, b, n, n_sims, rho, rng)
        for test, p in _pvalues(x, y, pareado).items():
            rejections = int((p < alpha).sum())
            rate = rejections / n_sims
            center = (rate + z**2 / (2 * n_sims)) / (1 + z**2 / n_sims)
            half = z / (1 + z**2 / n_sims) * np.sqrt(rate * (1 - rate) / n_sims + z**2 / (4 * n_sims**2))
            rows.append(
                {"n": n, "teste": test, "rejeicoes": rejections, "n_sims": n_sims, "poder": rate,
                 "ic95_low": center - half, "ic95_high": center + half, "alpha": alpha}
            )
    return pd.DataFrame(rows)


def required_n(power: pd.DataFrame, target: float = PODER_ALVO) -> pd.DataFrame:
    """Menor n simulado que atinge o poder alvo em cada teste (NaN se nenhum atingir)."""
    rows = []
    for test, group in power.groupby("teste", sort=True):
        reached = group.loc[group["poder"] >= target, "n"]
        rows.append({"teste": test, "poder_alvo": target, "n_necessario": reached.min() if len(reached) else np.nan})
    return pd.DataFrame(rows)
