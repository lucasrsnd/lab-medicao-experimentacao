"""Bônus — simulador interativo de poder: o usuário escolhe situação, n e ρ.

``simulate`` é pura (testável sem Streamlit) e reaproveita o motor Monte Carlo
oficial com menos repetições. ``render`` roda dentro de um ``st.fragment``: mexer
nos controles recalcula só este bloco, e a curva de cada (situação, n) fica em
cache, então mudar ρ não recalcula nada.
"""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import streamlit as st

from lab04.config import ALPHA, N_REAL, N_SIMS, SEED, TESTS
from lab04.contracts import Scenario
from lab04.dashboard import theme
from lab04.plots import g4_poder
from lab04.simulation import scenarios
from lab04.simulation.montecarlo import rejection_rates
from lab04.simulation.violations import register_violations
from lab04.style import TEST_COLORS

INTERACTIVE_SIMS = 1_000
EFFECT_GRID = tuple(round(0.1 * i, 1) for i in range(9))  # 0,0 … 0,8
N_MIN, N_MAX, N_STEP = 10, 150, 10
# A "amostra pequena" é a mesma situação realista com n = 10: aqui o n é o controle.
EXCLUDED = {"amostra_pequena"}


def interactive_scenarios() -> list[Scenario]:
    register_violations()
    return [s for s in scenarios.all_scenarios() if s.name not in EXCLUDED]


def simulate(scenario_name: str, n: int, n_sims: int = INTERACTIVE_SIMS, seed: int = SEED) -> pd.DataFrame:
    """Curva de poder (formato de ``simulacoes.csv``) da situação com ``n`` classes."""
    if not N_MIN <= n <= N_MAX:
        raise ValueError(f"n deve estar entre {N_MIN} e {N_MAX}.")
    register_violations()
    base = scenarios.get(scenario_name)
    return rejection_rates([replace(base, n=n)], EFFECT_GRID, n_sims, ALPHA, seed)


def at_effect(results: pd.DataFrame, rho: float) -> dict[str, pd.Series]:
    rows = results[results["effect"].round(1) == round(rho, 1)]
    return {test: rows[rows["test"] == test].iloc[0] for test in TESTS}


@st.cache_data(show_spinner=False, max_entries=64)
def _cached_simulate(scenario_name: str, n: int) -> pd.DataFrame:
    return simulate(scenario_name, n)


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def _thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


@st.fragment
def render() -> None:
    options = {s.name: s.label for s in interactive_scenarios()}
    left, middle, right = st.columns(3)
    name = left.selectbox("Situação", list(options), format_func=options.get, key="sim-situacao")
    n = middle.slider("Tamanho da amostra (n classes)", N_MIN, N_MAX, N_REAL, step=N_STEP, key="sim-n")
    rho = right.select_slider(
        "Tamanho do efeito (ρ latente)", options=EFFECT_GRID, value=0.3, key="sim-rho",
        format_func=lambda v: f"{v:.1f}".replace(".", ","),
    )
    with st.spinner(f"Simulando {_thousands(INTERACTIVE_SIMS)} repetições por ponto…"):
        results = _cached_simulate(name, n)

    point = at_effect(results, rho)
    kind = "Erro tipo I" if rho == 0 else "Poder"
    cards = st.columns(3)
    for col, test in zip(cards, TESTS):
        row = point[test]
        with col, st.container(key=f"card-sim-{test}"):
            theme.kpi(
                # Sem o símbolo do teste: o cabeçalho em maiúsculas transformaria ρ em Ρ.
            f"{kind} — {test.capitalize()}", _pct(row["rate"]),
                f"IC 95%: {_pct(row['ci_low'])} a {_pct(row['ci_high'])}",
                "Proporção das repetições em que o teste rejeitou H₀ (α = 5%).",
            )
    diff = (point["spearman"]["rate"] - point["pearson"]["rate"]) * 100
    leader = "Spearman" if diff > 0 else "Pearson"
    with cards[2], st.container(key="card-sim-diff"):
        theme.kpi(
            "Diferença", f"{abs(diff):.1f}".replace(".", ",") + " p.p.",
            f"a favor do {leader}" if abs(diff) >= 0.05 else "empate",
            "Diferença entre as taxas dos dois testes, em pontos percentuais.",
        )

    fig = g4_poder.figure(results, title=f"Poder com n = {n} — {options[name]}")
    fig.add_vline(x=rho, line={"color": "#2B2D3A", "width": 1.5, "dash": "dash"})
    for test in TESTS:  # destaca o ρ escolhido em cada curva
        fig.add_scatter(
            x=[rho], y=[point[test]["rate"] * 100], mode="markers", showlegend=False, hoverinfo="skip",
            marker={"size": 15, "color": TEST_COLORS[test], "symbol": g4_poder.SYMBOL[test],
                    "line": {"color": "#2B2D3A", "width": 2}},
        )
    fig.update_layout(height=430, margin={"l": 90, "t": 70})
    fig.layout.annotations[0].text = ""  # o título do painel repete o do gráfico
    st.plotly_chart(fig, width="stretch", theme=None)
    st.caption(
        f"{_thousands(INTERACTIVE_SIMS)} repetições por ponto (margem de até ±3 p.p.), semente {SEED}. "
        f"Os gráficos G3 e G4 usam {_thousands(N_SIMS)} repetições; aqui a curva é recalculada para o n escolhido."
    )
