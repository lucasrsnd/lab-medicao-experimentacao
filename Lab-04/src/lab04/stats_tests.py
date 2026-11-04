"""Testes de correlação e cálculo vetorizado de p-valores."""

from __future__ import annotations

import numpy as np
from scipy import stats

from lab04.config import TESTS
from lab04.contracts import TestResult


def _validate_pair(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if x_array.ndim != 1 or y_array.ndim != 1 or x_array.shape != y_array.shape:
        raise ValueError("x e y devem ser vetores unidimensionais do mesmo tamanho.")
    if x_array.size < 4:
        raise ValueError("São necessárias ao menos 4 observações.")
    if not np.isfinite(x_array).all() or not np.isfinite(y_array).all():
        raise ValueError("x e y devem conter apenas valores finitos.")
    if np.ptp(x_array) == 0 or np.ptp(y_array) == 0:
        raise ValueError("Não é possível calcular correlação para uma variável constante.")
    return x_array, y_array


def _build_result(test: str, effect: float, p_value: float, n: int) -> TestResult:
    if abs(effect) == 1.0:
        statistic = float(np.copysign(np.inf, effect))
    else:
        statistic = float(effect * np.sqrt((n - 2) / (1.0 - effect**2)))
    clipped_effect = float(np.clip(effect, -np.nextafter(1.0, 0.0), np.nextafter(1.0, 0.0)))
    fisher_z = np.arctanh(clipped_effect)
    margin = 1.959963984540054 / np.sqrt(n - 3)
    ci_low, ci_high = np.tanh((fisher_z - margin, fisher_z + margin))
    return TestResult(
        test=test,
        statistic=statistic,
        p_value=float(p_value),
        effect=float(effect),
        ci_low=float(min(ci_low, effect)),
        ci_high=float(max(ci_high, effect)),
        n=n,
    )


def pearson(x: np.ndarray, y: np.ndarray) -> TestResult:
    """Calcula Pearson r, teste bicaudal t com n−2 g.l. e IC de Fisher."""
    x_array, y_array = _validate_pair(x, y)
    result = stats.pearsonr(x_array, y_array)
    return _build_result("pearson", float(result.statistic), float(result.pvalue), x_array.size)


def spearman(x: np.ndarray, y: np.ndarray) -> TestResult:
    """Calcula Spearman ρ (postos médios em empates) e IC aproximado de Fisher."""
    x_array, y_array = _validate_pair(x, y)
    result = stats.spearmanr(x_array, y_array)
    return _build_result("spearman", float(result.statistic), float(result.pvalue), x_array.size)


def _row_correlations(x: np.ndarray, y: np.ndarray, test: str) -> np.ndarray:
    if test == "spearman":
        x = stats.rankdata(x, axis=1, method="average")
        y = stats.rankdata(y, axis=1, method="average")
    x_centered = x - x.mean(axis=1, keepdims=True)
    y_centered = y - y.mean(axis=1, keepdims=True)
    numerator = np.einsum("ij,ij->i", x_centered, y_centered)
    denominator = np.sqrt(
        np.einsum("ij,ij->i", x_centered, x_centered)
        * np.einsum("ij,ij->i", y_centered, y_centered)
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        return numerator / denominator


def pvalues(test: str, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Calcula p-valores bicaudais por linha sem iterar pelas repetições."""
    if test not in TESTS:
        raise ValueError(f"test deve ser um de {TESTS}.")
    x_array = np.asarray(X, dtype=float)
    y_array = np.asarray(Y, dtype=float)
    if x_array.ndim != 2 or y_array.ndim != 2 or x_array.shape != y_array.shape:
        raise ValueError("X e Y devem ser matrizes bidimensionais de mesmo formato.")
    if x_array.shape[0] < 1 or x_array.shape[1] < 4:
        raise ValueError("X e Y devem conter repetições com pelo menos 4 observações.")
    if not np.isfinite(x_array).all() or not np.isfinite(y_array).all():
        raise ValueError("X e Y devem conter apenas valores finitos.")

    effects = _row_correlations(x_array, y_array, test)
    if np.isnan(effects).any():
        raise ValueError("Cada linha de X e Y deve ter variância positiva.")
    perfect = np.abs(effects) >= 1.0
    statistic = np.empty_like(effects)
    statistic[perfect] = np.inf
    np.divide(
        np.abs(effects) * np.sqrt(x_array.shape[1] - 2),
        np.sqrt(1.0 - effects**2),
        out=statistic,
        where=~perfect,
    )
    return 2.0 * stats.t.sf(statistic, df=x_array.shape[1] - 2)
