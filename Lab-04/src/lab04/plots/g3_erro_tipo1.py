"""G3 — erro tipo I: taxa de rejeição com efeito 0, por situação e por teste.

Com ρ = 0, H₀ é verdadeira, então toda rejeição é falso positivo. Um teste bem
calibrado rejeita em torno de α (5%); a barra de erro é o IC 95% da taxa
estimada pelas repetições. IC inteiro acima de α = teste liberal; inteiro abaixo
= conservador.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from lab04.config import ALPHA, TESTS
from lab04.contracts import SIMULATION_COLUMNS
from lab04.style import REFERENCE_COLOR, TEST_COLORS, TEST_LABELS, apply_layout

CLOSE, LIBERAL, CONSERVATIVE = "perto de α", "liberal", "conservador"
VERDICT_LABELS = {CLOSE: "perto de 5%", LIBERAL: "liberal (> 5%)", CONSERVATIVE: "conservador (< 5%)"}


def type1_rows(results: pd.DataFrame) -> pd.DataFrame:
    """Linhas com efeito 0 (H₀ verdadeira), validando o formato de ``simulacoes.csv``."""
    missing = set(SIMULATION_COLUMNS) - set(results.columns)
    if missing:
        raise ValueError(f"results sem as colunas {sorted(missing)}.")
    rows = results[results["effect"] == 0]
    if rows.empty:
        raise ValueError("results não tem linhas com effect == 0 (erro tipo I).")
    unknown = set(rows["test"]) - set(TESTS)
    if unknown:
        raise ValueError(f"Testes desconhecidos em results: {sorted(unknown)}.")
    if rows.duplicated(["scenario", "test"]).any():
        raise ValueError("Há mais de uma linha com effect == 0 por cenário e teste.")
    return rows


def classify(results: pd.DataFrame) -> pd.DataFrame:
    """Veredito por cenário e teste: ``perto de α``, ``liberal`` ou ``conservador``.

    Compara α com o IC 95% da taxa de rejeição sob H₀.
    """
    rows = type1_rows(results).copy()
    alpha = rows["alpha"]
    rows["verdict"] = CLOSE
    rows.loc[rows["ci_low"] > alpha, "verdict"] = LIBERAL
    rows.loc[rows["ci_high"] < alpha, "verdict"] = CONSERVATIVE
    return rows[["scenario", "label", "n", "test", "rate", "ci_low", "ci_high", "alpha", "verdict"]]


def figure(results: pd.DataFrame) -> go.Figure:
    """Barras agrupadas (um grupo por cenário, uma barra por teste) com IC e linha em α."""
    rows = type1_rows(results)
    # Ordem de aparição no arquivo: o cenário realista vem antes das violações.
    scenarios = rows.drop_duplicates("scenario")[["scenario", "label", "n"]]
    categories = [f"{r.label}<br>n = {r.n}" for r in scenarios.itertuples()]
    alphas = rows["alpha"].unique()
    if len(alphas) != 1:
        raise ValueError("results mistura níveis de significância (coluna alpha).")
    alpha = float(alphas[0])

    fig = go.Figure()
    for test in TESTS:
        sub = rows[rows["test"] == test].set_index("scenario").reindex(scenarios["scenario"])
        if sub["rate"].isna().any():
            raise ValueError(f"Falta a taxa de {test} em algum cenário.")
        rate = sub["rate"] * 100
        fig.add_trace(
            go.Bar(
                name=TEST_LABELS[test],
                x=categories,
                y=rate,
                marker_color=TEST_COLORS[test],
                error_y={
                    "type": "data",
                    "symmetric": False,
                    "array": ((sub["ci_high"] * 100) - rate).clip(lower=0),
                    "arrayminus": (rate - (sub["ci_low"] * 100)).clip(lower=0),
                    "color": "#333333",
                    "thickness": 1.5,
                },
                customdata=sub[["ci_low", "ci_high", "rejections", "n_sims"]] * [100, 100, 1, 1],
                hovertemplate=(
                    "%{x}<br>%{y:.2f}% das repetições rejeitaram H₀<br>"
                    "IC 95%: [%{customdata[0]:.2f}%; %{customdata[1]:.2f}%]<br>"
                    "%{customdata[2]:.0f} de %{customdata[3]:.0f}<extra>" + TEST_LABELS[test] + "</extra>"
                ),
            )
        )
    fig.add_hline(
        y=alpha * 100,
        line={"color": REFERENCE_COLOR, "width": 2, "dash": "dash"},
        annotation_text=f"α = {alpha * 100:.0f}% (taxa esperada sob H₀)".replace(".", ","),
        annotation_position="top right",
        annotation_font={"color": REFERENCE_COLOR},
    )
    apply_layout(
        fig,
        "G3 — Erro tipo I: taxa de rejeição com ρ = 0 (H₀ verdadeira)",
        "Situação simulada",
        "Taxa de rejeição de H₀ (%)",
    )
    fig.update_layout(barmode="group", height=480)
    fig.update_yaxes(rangemode="tozero", ticksuffix="%")
    return fig
