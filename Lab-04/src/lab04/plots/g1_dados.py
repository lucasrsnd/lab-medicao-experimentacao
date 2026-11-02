"""G1 — dados reais ao lado dos dados simulados (histogramas de LOC e de defeitos)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lab04.contracts import SIMULATED_COLUMNS
from lab04.style import DATA_COLORS, apply_layout

LOC_TICKS = (10, 100, 1_000, 10_000)
Y_TITLE = "Proporção de módulos (0–1)"
X_TITLES = {
    "loc": "LOC (linhas de código, escala log)",
    "defects": "Defeitos por módulo (contagem)",
}


def _check(df: pd.DataFrame, name: str) -> None:
    missing = set(SIMULATED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{name} sem as colunas {sorted(missing)}.")
    if df.empty:
        raise ValueError(f"{name} está vazio.")
    if (df["loc"] <= 0).any():
        raise ValueError(f"{name}: LOC deve ser positiva para a escala log.")


def figure(real: pd.DataFrame, simulated: pd.DataFrame) -> go.Figure:
    """Grade 2×2: linhas = LOC e defeitos; colunas = dados reais e simulados.

    Cada histograma usa a proporção de módulos por faixa, o que torna comparáveis
    uma amostra pequena (real) e um conjunto grande (simulado). Os limites dos
    eixos e as faixas são compartilhados entre real e simulado.
    """
    _check(real, "real")
    _check(simulated, "simulated")

    log_all = np.log10(np.concatenate([real["loc"], simulated["loc"]]).astype(float))
    loc_bins = {
        "start": float(np.floor(log_all.min() * 4) / 4),
        "end": float(np.ceil(log_all.max() * 4) / 4),
        "size": 0.25,
    }
    defects_max = int(max(real["defects"].max(), simulated["defects"].max()))

    panels = (("Real", "real"), ("Simulado", "simulado"))
    titles = [f"LOC — {label}" for label, _ in panels] + [
        f"Defeitos — {label}" for label, _ in panels
    ]
    fig = make_subplots(rows=2, cols=2, subplot_titles=titles, vertical_spacing=0.18)

    for col, (label, key) in enumerate(panels, start=1):
        data = real if key == "real" else simulated
        legend = {"name": f"{label} (n = {len(data):,})".replace(",", "."), "legendgroup": key}
        fig.add_trace(
            go.Histogram(
                x=np.log10(data["loc"].astype(float)),
                xbins=loc_bins,
                histnorm="probability",
                marker={"color": DATA_COLORS[key], "line": {"color": "white", "width": 0.5}},
                **legend,
            ),
            row=1,
            col=col,
        )
        fig.add_trace(
            go.Histogram(
                x=data["defects"],
                xbins={"start": -0.5, "end": defects_max + 0.5, "size": 1},
                histnorm="probability",
                marker={"color": DATA_COLORS[key], "line": {"color": "white", "width": 0.5}},
                showlegend=False,
                **legend,
            ),
            row=2,
            col=col,
        )

    apply_layout(fig, "G1 — Dados reais × dados simulados", X_TITLES["loc"], Y_TITLE)
    for col in (1, 2):
        fig.update_xaxes(
            title_text=X_TITLES["loc"],
            tickvals=[np.log10(t) for t in LOC_TICKS],
            ticktext=[f"{t:,}".replace(",", ".") for t in LOC_TICKS],
            row=1,
            col=col,
        )
        fig.update_xaxes(title_text=X_TITLES["defects"], dtick=1, row=2, col=col)
    # Mesma escala entre real e simulado, em cada linha.
    fig.update_xaxes(matches="x", row=1, col=2)
    fig.update_xaxes(matches="x3", row=2, col=2)
    fig.update_yaxes(matches="y", row=1, col=2)
    fig.update_yaxes(matches="y3", row=2, col=2)
    fig.update_layout(
        height=660,
        bargap=0.05,
        margin={"l": 70, "r": 20, "t": 80, "b": 110},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.2, "x": 0.0},
    )
    return fig
