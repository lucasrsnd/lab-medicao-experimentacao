"""G2 — distribuição da estatística t sob H0, região de rejeição e p-valor do exemplo.

Pearson e Spearman usam a mesma referência: t = r·√((n−2)/(1−r²)) com n−2 g.l.
Opcionalmente sobrepõe a distribuição nula por permutação dos próprios dados,
que mostra se a aproximação t vale para dados assimétricos e com empates.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from scipy import stats

from lab04.config import ALPHA, SEED, TESTS
from lab04.style import TEST_COLORS, TEST_LABELS, apply_layout

CURVE_COLOR = "#333333"
REJECTION_COLOR = "#6B6B6B"
PERMUTATION_COLOR = "#BDBDBD"
GRID_POINTS = 801


def _check(test: str, n: int) -> None:
    if test not in TESTS:
        raise ValueError(f"test deve ser um de {TESTS}.")
    if n < 4:
        raise ValueError("n deve ser >= 4.")


def _num(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def critical_value(n: int, alpha: float = ALPHA) -> float:
    """|t| a partir do qual o teste bicaudal rejeita H0."""
    return float(stats.t.ppf(1.0 - alpha / 2.0, n - 2))


def p_value(n: int, observed_statistic: float) -> float:
    """p-valor bicaudal: área da t(n−2) além de ±|t observado|."""
    return float(2.0 * stats.t.sf(abs(observed_statistic), n - 2))


def permutation_null(
    test: str,
    x: np.ndarray,
    y: np.ndarray,
    n_perm: int = 5_000,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Estatísticas t obtidas embaralhando ``y``: a nula exata condicionada aos dados."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    _check(test, x.size)
    if x.shape != y.shape or x.ndim != 1:
        raise ValueError("x e y devem ser vetores do mesmo tamanho.")
    rng = rng if rng is not None else np.random.default_rng(SEED)
    if test == "spearman":
        x, y = stats.rankdata(x), stats.rankdata(y)
    permuted = rng.permuted(np.broadcast_to(y, (n_perm, y.size)), axis=1)
    xc = x - x.mean()
    yc = permuted - permuted.mean(axis=1, keepdims=True)
    r = (yc @ xc) / np.sqrt((xc @ xc) * np.einsum("ij,ij->i", yc, yc))
    r = np.clip(r, -1 + 1e-12, 1 - 1e-12)
    return r * np.sqrt((x.size - 2) / (1.0 - r**2))


def _tail_traces(xs: np.ndarray, df: int, threshold: float, **style) -> list[go.Scatter]:
    """Áreas sob a t(df) em x <= −threshold e x >= threshold (uma entrada na legenda)."""
    traces = []
    for side in (-1, 1):
        # Inclui o próprio limiar para a área começar exatamente nele.
        tail_x = np.sort(np.append(xs[side * xs > threshold], side * threshold))
        traces.append(
            go.Scatter(x=tail_x, y=stats.t.pdf(tail_x, df), showlegend=side == 1, **style)
        )
    return traces


def figure(
    test: str,
    n: int,
    observed_statistic: float,
    alpha: float = ALPHA,
    null_statistics: np.ndarray | None = None,
) -> go.Figure:
    """G2 de um teste: curva t(n−2) sob H0, rejeição bicaudal hachurada e p-valor como área."""
    _check(test, n)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha deve estar em (0, 1).")
    df = n - 2
    crit = critical_value(n, alpha)
    t_obs = float(np.clip(observed_statistic, -50.0, 50.0))
    p = p_value(n, t_obs)

    limit = max(4.5, abs(t_obs) * 1.15 + 0.5)
    if null_statistics is not None and len(null_statistics):
        limit = max(limit, float(np.quantile(np.abs(null_statistics), 0.995)))
    xs = np.linspace(-limit, limit, GRID_POINTS)

    fig = go.Figure()
    if null_statistics is not None and len(null_statistics):
        # Histograma em degrau translúcido: não esconde a hachura nem a área do p-valor.
        density, edges = np.histogram(
            null_statistics, bins=np.arange(-limit, limit + 0.2, 0.2), density=True
        )
        fig.add_trace(
            go.Scatter(
                x=edges, y=np.append(density, density[-1]), mode="lines",
                line={"shape": "hv", "color": PERMUTATION_COLOR, "width": 1.5},
                fill="tozeroy", fillcolor="rgba(189,189,189,0.35)",
                name=f"Nula por permutação dos dados ({len(null_statistics):,} rep.)".replace(",", "."),
                hovertemplate="t ≈ %{x:.1f}<br>densidade %{y:.3f}<extra>permutação</extra>",
            )
        )
    for trace in _tail_traces(
        xs, df, crit, fill="tozeroy", mode="none",
        fillcolor="rgba(107,107,107,0.10)",
        fillpattern={"shape": "/", "fgcolor": REJECTION_COLOR, "size": 8, "solidity": 0.25},
        name=f"Região de rejeição (|t| > {_num(crit, 2)}, α = {_num(alpha * 100, 0)}%)",
        legendgroup="rejeicao", hoverinfo="skip",
    ):
        fig.add_trace(trace)
    for trace in _tail_traces(
        xs, df, abs(t_obs), fill="tozeroy", mode="none",
        fillcolor=TEST_COLORS[test], opacity=0.9,
        name=f"p-valor = {_num(p, 4)} (área além de ±t)",
        legendgroup="pvalor", hoverinfo="skip",
    ):
        fig.add_trace(trace)
    fig.add_trace(
        go.Scatter(
            x=xs, y=stats.t.pdf(xs, df), mode="lines",
            line={"color": CURVE_COLOR, "width": 2},
            name=f"t com {df} g.l. sob H₀",
            hovertemplate="t = %{x:.2f}<br>densidade %{y:.3f}<extra>t(" + str(df) + ")</extra>",
        )
    )
    fig.add_vline(x=t_obs, line={"color": TEST_COLORS[test], "width": 2})
    fig.add_annotation(
        x=t_obs, y=0.98, yref="paper", yanchor="top", text=f"t observado = {_num(t_obs, 2)}",
        showarrow=False, xanchor="left" if t_obs >= 0 else "right", xshift=6 if t_obs >= 0 else -6,
        font={"color": CURVE_COLOR, "size": 13}, bgcolor="rgba(255,255,255,0.8)",
    )
    # Seta para a cauda: com p pequeno a área colorida é estreita demais para ver sozinha.
    tail_x = abs(t_obs) + 0.1
    fig.add_annotation(
        x=tail_x, y=stats.t.pdf(tail_x, df) / 2, ax=40, ay=-55,
        text="área colorida = p-valor", showarrow=True, arrowhead=2, arrowwidth=1.5,
        arrowcolor=CURVE_COLOR, font={"color": CURVE_COLOR, "size": 13},
        bgcolor="rgba(255,255,255,0.8)",
    )
    apply_layout(
        fig,
        f"G2 — {TEST_LABELS[test]}: estatística t sob H₀ (n = {n})",
        "Estatística t do teste (adimensional)",
        "Densidade de probabilidade",
    )
    fig.update_layout(
        height=480,
        legend={"orientation": "h", "yanchor": "top", "y": -0.27, "x": 0.0},
        margin={"l": 60, "r": 20, "t": 60, "b": 150},
    )
    fig.update_yaxes(rangemode="tozero")
    return fig
