"""G4 — curvas de poder: proporção de rejeições × tamanho do efeito, por situação.

Um painel por situação simulada (Q2 e Q3), com os dois testes no mesmo painel e
as mesmas cores dos demais gráficos. Em ρ = 0 a curva mostra o erro tipo I (G3);
a linha pontilhada marca o poder de 80%, referência usual de planejamento.
"""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lab04.config import TESTS
from lab04.contracts import SIMULATION_COLUMNS
from lab04.style import TEST_COLORS, TEST_LABELS, apply_layout

TARGET_POWER = 0.8
REFERENCE_GRAY = "#8A94A6"
# Segunda codificação além da cor: traço e símbolo por teste.
DASH = {"pearson": "solid", "spearman": "dash"}
SYMBOL = {"pearson": "circle", "spearman": "diamond"}
TITLE = "G4 — Poder: proporção de rejeições de H₀ × tamanho do efeito"
X_TITLE = "Correlação latente ρ"
Y_TITLE = "Rejeições de H₀ (%)"
MAX_COLUMNS = 4


def _check(results: pd.DataFrame) -> None:
    missing = set(SIMULATION_COLUMNS) - set(results.columns)
    if missing:
        raise ValueError(f"results sem as colunas {sorted(missing)}.")
    if results.empty:
        raise ValueError("results está vazio.")
    unknown = set(results["test"]) - set(TESTS)
    if unknown:
        raise ValueError(f"Testes desconhecidos em results: {sorted(unknown)}.")
    if results.duplicated(["scenario", "effect", "test"]).any():
        raise ValueError("Há mais de uma linha por cenário, efeito e teste.")
    if results.groupby("scenario")["effect"].nunique().min() < 2:
        raise ValueError("Cada cenário precisa de ao menos 2 tamanhos de efeito para formar a curva.")


def panel_title(label: str, n: int) -> str:
    # Quebra de linha antes do n: com 4 painéis lado a lado, títulos longos se tocariam.
    return label if f"n = {n}" in label else f"{label}<br>n = {n}"


def figure(results: pd.DataFrame, title: str = TITLE) -> go.Figure:
    """Pequenos múltiplos (um por cenário, na ordem do arquivo) com poder ± IC 95%."""
    _check(results)
    scenarios = results.drop_duplicates("scenario")[["scenario", "label", "n"]]
    columns = min(len(scenarios), MAX_COLUMNS)
    rows = math.ceil(len(scenarios) / columns)
    fig = make_subplots(
        rows=rows, cols=columns, shared_yaxes=True,
        subplot_titles=[panel_title(s.label, s.n) for s in scenarios.itertuples()],
        horizontal_spacing=0.04, vertical_spacing=0.22 if rows > 1 else 0.0,
    )
    for i, scenario in enumerate(scenarios.itertuples()):
        row, col = divmod(i, columns)
        for test in TESTS:
            sub = results[(results["scenario"] == scenario.scenario) & (results["test"] == test)]
            sub = sub.sort_values("effect")
            rate = sub["rate"] * 100
            fig.add_trace(
                go.Scatter(
                    x=sub["effect"], y=rate, mode="lines+markers",
                    name=TEST_LABELS[test], legendgroup=test, showlegend=i == 0,
                    line={"color": TEST_COLORS[test], "width": 2.5, "dash": DASH[test]},
                    marker={"size": 8, "symbol": SYMBOL[test], "line": {"color": "white", "width": 1.5}},
                    error_y={
                        "type": "data", "symmetric": False,
                        "array": (sub["ci_high"] * 100 - rate).clip(lower=0),
                        "arrayminus": (rate - sub["ci_low"] * 100).clip(lower=0),
                        "color": TEST_COLORS[test], "thickness": 1.2, "width": 3,
                    },
                    customdata=sub[["ci_low", "ci_high"]] * 100,
                    hovertemplate=(
                        "ρ = %{x:.1f}<br>rejeitou H₀ em %{y:.1f}% das repetições<br>"
                        "IC 95%: [%{customdata[0]:.1f}%; %{customdata[1]:.1f}%]"
                        "<extra>" + TEST_LABELS[test] + "</extra>"
                    ),
                ),
                row=row + 1, col=col + 1,
            )
        fig.add_hline(
            y=TARGET_POWER * 100, row=row + 1, col=col + 1,
            line={"color": REFERENCE_GRAY, "width": 1.5, "dash": "dot"},
        )

    apply_layout(fig, title, X_TITLE, Y_TITLE)
    effects = sorted(results["effect"].unique())
    fig.update_xaxes(tickvals=effects, tickformat=".1f", range=[min(effects) - 0.04, max(effects) + 0.04])
    fig.update_yaxes(range=[0, 100], ticksuffix="%", title_text="")
    for row in range(1, rows + 1):
        fig.update_yaxes(title_text=Y_TITLE, row=row, col=1)
    fig.add_annotation(
        text=f"poder de {TARGET_POWER:.0%}", xref="x domain", yref="y", x=0.02, y=TARGET_POWER * 100,
        yanchor="bottom", showarrow=False, font={"color": REFERENCE_GRAY, "size": 12},
    )
    fig.update_layout(
        height=360 * rows + 120,
        legend={"orientation": "h", "yanchor": "top", "y": -0.18 if rows == 1 else -0.08, "x": 0.0},
        margin={"l": 70, "r": 20, "t": 130, "b": 110},  # títulos de painel em 2 linhas
    )
    return fig
