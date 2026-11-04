"""Dashboard do Lab04 — Pearson × Spearman (par P5).

Executar no diretório Lab-04:  streamlit run src/lab04/dashboard/app.py

A página só lê artefatos versionados (data/, outputs/, docs/dashboard/); nada
de simulação pesada acontece ao abrir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lab04.config import ALPHA, DASHBOARD_URL, N_SIMS, PROJECTS_URL, REPO_URL, SEED, TESTS
from lab04.dashboard import content
from lab04.plots import g1_dados, g2_nula
from lab04.simulation.scenarios import get as get_scenario
from lab04.style import TEST_LABELS

SECTIONS = (
    ("cenario", "1. Cenário"),
    ("dados", "2. Os dados"),
    ("testes", "3. Como os testes funcionam"),
    ("erro-tipo-i", "4. Erro tipo I"),
    ("poder", "5. Poder"),
    ("dados-reais", "6. Dados reais"),
    ("conclusao", "7. Conclusão"),
)
N_PERMUTATIONS = 5_000


def num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def header(key: str) -> None:
    st.header(dict(SECTIONS)[key], anchor=key)


def text(name: str) -> None:
    body = content.section_text(name)
    if body:
        st.markdown(body)
    else:
        st.info(f"Texto pendente: `docs/dashboard/{name}.md`.")


def chart(fig: go.Figure) -> None:
    # theme=None mantém o tema claro e as cores definidas em lab04.style.
    st.plotly_chart(fig, width="stretch", theme=None)


def pending(what: str) -> None:
    st.info(f"Disponível na próxima entrega: {what}.")


@st.cache_data
def load_g1_simulated() -> pd.DataFrame | None:
    real = content.real_params()
    return content.g1_simulated(real.params) if real else None


@st.cache_data
def load_permutation_nulls() -> dict[str, np.ndarray] | None:
    ex = content.example()
    if ex is None:
        return None
    sample = content.example_sample(ex, get_scenario("realista").params)
    return {
        test: g2_nula.permutation_null(
            test, sample["loc"].to_numpy(), sample["defects"].to_numpy(),
            n_perm=N_PERMUTATIONS, rng=np.random.default_rng(SEED),
        )
        for test in TESTS
    }


def links() -> None:
    dashboard = f"[{DASHBOARD_URL}]({DASHBOARD_URL})" if DASHBOARD_URL else "execução local (publicação na entrega final)"
    st.markdown(
        f"**Dashboard:** {dashboard} · **Repositório:** [{REPO_URL}]({REPO_URL}) · "
        f"**GitHub Projects:** [{PROJECTS_URL}]({PROJECTS_URL})"
    )


def sidebar() -> None:
    with st.sidebar:
        st.subheader("Seções")
        st.markdown("\n".join(f"- [{label}](#{key})" for key, label in SECTIONS))
        st.subheader("Reprodução")
        st.markdown(
            f"Semente **{SEED}** · α = **{num(ALPHA * 100, 0)}%** bicaudal · "
            f"**{N_SIMS:,}** repetições por situação".replace(",", ".")
        )


def section_scenario(real: content.RealParams | None) -> None:
    header("cenario")
    text("01-cenario")
    if real is None:
        pending("parâmetros dos dados reais (`outputs/real_params.json`)")
        return
    cols = st.columns(4)
    cols[0].metric("Classes na amostra real", real.n)
    cols[1].metric("Classes sem defeito", f"{num(real.observed['prop_zeros'] * 100, 0)}%")
    cols[2].metric("Assimetria de LOC", num(real.observed["assimetria_loc"]))
    cols[3].metric("Teste", f"Bicaudal, α = {num(ALPHA * 100, 0)}%")
    st.caption(f"Fonte: {real.source}.")


def section_data(real: content.RealParams | None) -> None:
    header("dados")
    sample, simulated = content.real_sample(), load_g1_simulated()
    if sample is None or simulated is None:
        pending("G1 (amostra real e parâmetros)")
    else:
        chart(g1_dados.figure(sample, simulated))
    text("02-dados")
    if real is not None:
        with st.expander("Parâmetros da simulação estimados dos dados reais"):
            p = real.params
            st.table(pd.DataFrame([
                {"Variável": "LOC", "Distribuição": "Lognormal",
                 "Parâmetros": f"μ = {num(p.loc_mu)} (mediana ≈ {np.exp(p.loc_mu):.0f} linhas), σ = {num(p.loc_sigma)}"},
                {"Variável": "Defeitos", "Distribuição": "Binomial negativa",
                 "Parâmetros": f"média = {num(p.defects_mean)}, dispersão k = {num(p.defects_dispersion)}"},
            ]))


def section_tests() -> None:
    header("testes")
    ex, nulls = content.example(), load_permutation_nulls()
    if ex is None or nulls is None:
        pending("G2 (`outputs/exemplo_simulado.json`)")
        text("03-testes")
        return
    st.markdown(
        f"Exemplo: **um** conjunto simulado com n = {ex.n}, correlação latente ρ = {num(ex.rho, 1)} "
        f"(H₁ verdadeira) e semente {ex.seed}."
    )
    cols = st.columns(2)
    for col, test in zip(cols, TESTS):
        with col:
            chart(g2_nula.figure(test, ex.n, ex.results[test].statistic, null_statistics=nulls[test]))
    st.table(pd.DataFrame([
        {
            "Teste": TEST_LABELS[t],
            "Compara": "valores (associação linear)" if t == "pearson" else "postos (associação monotônica)",
            "Correlação": num(r.effect, 3),
            "IC 95%": f"[{num(r.ci_low)}; {num(r.ci_high)}]",
            "t": num(r.statistic),
            "p-valor": num(r.p_value, 4),
            "Decisão (α = 5%)": "Rejeita H₀" if r.p_value < ALPHA else "Não rejeita H₀",
        }
        for t, r in ex.results.items()
    ]))
    text("03-testes")
    text("03-g2")


def main() -> None:
    st.set_page_config(page_title="Lab04 — Pearson × Spearman", layout="wide")
    st.title("Pearson × Spearman: tamanho do módulo e defeitos")
    links()
    sidebar()

    real = content.real_params()
    section_scenario(real)
    section_data(real)
    section_tests()

    header("erro-tipo-i")
    pending("G3 — erro tipo I por situação (Sprint 02, #164 e #167)")
    header("poder")
    pending("G4 — curvas de poder (Sprint 02, #164 e #168)")
    header("dados-reais")
    pending("tabela dos dois testes nos dados reais (entrega final, #171)")
    header("conclusao")
    pending("expectativa × resultado e recomendação (entrega final, #171)")


main()
