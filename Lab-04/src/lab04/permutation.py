"""Teste de permutação: a distribuição nula exata condicionada aos próprios dados.

Embaralhar ``y`` destrói qualquer associação com ``x`` mas mantém as marginais
(assimetria, zeros, empates). Serve de referência sem a aproximação t(n−2):
no G2 (forma da nula) e na seção 6 (p-valor dos dados reais).
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from lab04.config import SEED, TESTS


def permutation_null(
    test: str,
    x: np.ndarray,
    y: np.ndarray,
    n_perm: int = 5_000,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Estatísticas t obtidas embaralhando ``y``, uma por permutação."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if test not in TESTS:
        raise ValueError(f"test deve ser um de {TESTS}.")
    if x.shape != y.shape or x.ndim != 1:
        raise ValueError("x e y devem ser vetores do mesmo tamanho.")
    if x.size < 4:
        raise ValueError("São necessárias ao menos 4 observações.")
    rng = rng if rng is not None else np.random.default_rng(SEED)
    if test == "spearman":
        x, y = stats.rankdata(x), stats.rankdata(y)
    permuted = rng.permuted(np.broadcast_to(y, (n_perm, y.size)), axis=1)
    xc = x - x.mean()
    yc = permuted - permuted.mean(axis=1, keepdims=True)
    r = (yc @ xc) / np.sqrt((xc @ xc) * np.einsum("ij,ij->i", yc, yc))
    r = np.clip(r, -1 + 1e-12, 1 - 1e-12)
    return r * np.sqrt((x.size - 2) / (1.0 - r**2))


def permutation_pvalue(null_statistics: np.ndarray, observed_statistic: float) -> float:
    """p-valor bicaudal: fração das permutações com |t| ≥ |t observado|.

    Usa (k + 1) / (B + 1), que nunca devolve zero e é válido para B finito.
    """
    null_statistics = np.asarray(null_statistics)
    extreme = np.count_nonzero(np.abs(null_statistics) >= abs(observed_statistic) - 1e-12)
    return (extreme + 1) / (null_statistics.size + 1)
