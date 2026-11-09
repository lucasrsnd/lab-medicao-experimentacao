"""Seção 6 — poder × tamanho da amostra para os efeitos de referência dos dados reais.

Um painel por efeito (observado e conservador), os dois testes no mesmo painel,
a linha de 80% e uma linha vertical no n da amostra real.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS
from lab04.plots.g4_poder import DASH, REFERENCE_GRAY, SYMBOL, TARGET_POWER
from lab04.style import TEST_COLORS, TEST_LABELS, apply_layout

TITLE = "Poder × tamanho da amostra nos efeitos dos dados reais"
X_TITLE = "Tamanho da amostra (n classes)"
Y_TITLE = "Poder (%)"


def figure(curves: pd.DataFrame, panel_titles: dict[str, str], real_n: int) -> go.Figure:
    """``curves`` = poder_por_n.csv (coluna ``reference``); um painel por referência."""
    missing = ({"reference"} | set(SIMULATION_COLUMNS)) - set(curves.columns)
    if missing:
        raise ValueError(f"curves sem as colunas {sorted(missing)}.")
    references = list(dict.fromkeys(curves["reference"]))
    if set(references) - set(panel_titles):
        raise ValueError("Falta título para algum efeito de referência.")
    fig = make_subplots(rows=1, cols=len(references), shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=[panel_titles[r] for r in references])
    for col, reference in enumerate(references, start=1):
        for test in TESTS:
            sub = curves[(curves["reference"] == reference) & (curves["test"] == test)].sort_values("n")
            fig.add_trace(
                go.Scatter(
                    x=sub["n"], y=sub["rate"] * 100, mode="lines+markers",
                    name=TEST_LABELS[test], legendgroup=test, showlegend=col == 1,
                    line={"color": TEST_COLORS[test], "width": 2.5, "dash": DASH[test]},
                    marker={"size": 7, "symbol": SYMBOL[test], "line": {"color": "white", "width": 1.5}},
                    hovertemplate="n = %{x}<br>poder %{y:.1f}%<extra>" + TEST_LABELS[test] + "</extra>",
                ),
                row=1, col=col,
            )
        fig.add_hline(y=TARGET_POWER * 100, row=1, col=col,
                      line={"color": REFERENCE_GRAY, "width": 1.5, "dash": "dot"})
        fig.add_vline(x=real_n, row=1, col=col, line={"color": "#2B2D3A", "width": 1.2, "dash": "dash"})
    apply_layout(fig, TITLE, X_TITLE, Y_TITLE)
    fig.update_yaxes(range=[0, 102], ticksuffix="%", title_text="")
    fig.update_yaxes(title_text=Y_TITLE, row=1, col=1)
    # Na base do painel: no topo, as curvas do efeito observado já estão perto de 100%.
    fig.add_annotation(text=f"n real = {real_n}", x=real_n, xref="x", y=2, yref="y",
                       xanchor="left", yanchor="bottom", xshift=4, showarrow=False,
                       font={"size": 12, "color": "#2B2D3A"}, bgcolor="rgba(255,255,255,0.85)")
    fig.update_layout(height=430, margin={"l": 70, "r": 20, "t": 110, "b": 110},
                      legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0.0})
    return fig
