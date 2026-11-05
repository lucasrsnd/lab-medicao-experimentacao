"""G1 — dados reais ao lado dos dados simulados (histogramas de LOC e de defeitos)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lab04.contracts import SIMULATED_COLUMNS
from lab04.style import DATA_COLORS, apply_layout

LOC_TICKS = (10, 100, 1_000, 10_000)
# Defeitos >= DEFECTS_CAP entram numa única barra "10+": a cauda simulada chega a
# dezenas de defeitos e esticaria o eixo com barras quase vazias.
DEFECTS_CAP = 10
Y_TITLE = "Classes na faixa (%)"
X_TITLES = {
    "loc": "LOC por classe (linhas, escala log)",
    "defects": f"Defeitos por classe ({DEFECTS_CAP}+ agrupados)",
}
SUBPLOT_TITLES = ("Tamanho (LOC)", "Defeitos")


def _check(df: pd.DataFrame, name: str) -> None:
    missing = set(SIMULATED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{name} sem as colunas {sorted(missing)}.")
    if df.empty:
        raise ValueError(f"{name} está vazio.")
    if (df["loc"] <= 0).any():
        raise ValueError(f"{name}: LOC deve ser positiva para a escala log.")


def figure(real: pd.DataFrame, simulated: pd.DataFrame) -> go.Figure:
    """Dois painéis (LOC e defeitos) com barras real × simulado lado a lado.

    Cada histograma usa a proporção de classes por faixa, o que torna comparáveis
    uma amostra pequena (real) e um conjunto grande (simulado). Real e simulado
    usam as mesmas faixas, e as barras de cada faixa ficam adjacentes.
    """
    _check(real, "real")
    _check(simulated, "simulated")

    log_all = np.log10(np.concatenate([real["loc"], simulated["loc"]]).astype(float))
    loc_bins = {
        "start": float(np.floor(log_all.min() * 4) / 4),
        "end": float(np.ceil(log_all.max() * 4) / 4),
        "size": 0.25,
    }
    defects_bins = {"start": -0.5, "end": DEFECTS_CAP + 0.5, "size": 1}

    fig = make_subplots(rows=1, cols=2, subplot_titles=SUBPLOT_TITLES, horizontal_spacing=0.1)
    for label, key, data in (("Real", "real", real), ("Simulado", "simulado", simulated)):
        common = {
            "name": f"{label} (n = {len(data):,})".replace(",", "."),
            "legendgroup": key,
            "histnorm": "probability",
            "marker": {"color": DATA_COLORS[key], "line": {"color": "white", "width": 1}},
        }
        fig.add_trace(
            go.Histogram(
                x=np.log10(data["loc"].astype(float)), xbins=loc_bins,
                hovertemplate="%{y:.1%} das classes<extra>" + label + "</extra>", **common,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Histogram(
                x=np.minimum(data["defects"], DEFECTS_CAP), xbins=defects_bins, showlegend=False,
                hovertemplate="%{x} defeitos: %{y:.1%} das classes<extra>" + label + "</extra>",
                **common,
            ),
            row=1, col=2,
        )

    apply_layout(fig, "G1 — Dados reais × dados simulados", X_TITLES["loc"], Y_TITLE)
    fig.update_xaxes(
        tickvals=[np.log10(t) for t in LOC_TICKS],
        ticktext=[f"{t:,}".replace(",", ".") for t in LOC_TICKS],
        row=1, col=1,
    )
    fig.update_xaxes(
        title_text=X_TITLES["defects"],
        tickvals=list(range(DEFECTS_CAP + 1)),
        ticktext=[str(v) for v in range(DEFECTS_CAP)] + [f"{DEFECTS_CAP}+"],
        row=1, col=2,
    )
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_layout(
        barmode="group", bargap=0.2, bargroupgap=0.05, height=460,
        margin={"l": 70, "r": 20, "t": 80, "b": 110},
        legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0.0},
    )
    return fig
