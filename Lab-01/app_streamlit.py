"""
Dashboard interativo do Lab01 (Streamlit).

Reaproveita `src/analysis` - a mesma fonte de estatísticas usada pelas figuras
estáticas do relatório (`scripts/gerar_relatorio_figuras.py`), pra não duplicar
cálculo entre as duas apresentações. Cobertura: RQ01-RQ04 (#15, #16), RQ05-RQ07 (#17).

Uso (a partir de Lab-01/, com o venv ativado):
    pip install -r requirements.txt
    pip install -e .
    streamlit run app_streamlit.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis import stats
from src.analysis.referencias import OCTOVERSE_EDICAO, OCTOVERSE_FONTE_URL

DATASET_PATH = Path(__file__).resolve().parent / "data" / "raw" / "repositorios_s02.csv"
RQ07_PATH = Path(__file__).resolve().parent / "data" / "processed" / "rq07_resultado_agrupado.csv"

# Uma entrada por RQ numérica (histograma). RQ05/RQ07 têm formato diferente
# (categórico/agrupado) e ganham abas próprias, fora deste loop.
ABAS_NUMERICAS = [
    {"titulo": "RQ01 - Idade", "coluna": "idade_anos", "resumo": stats.resumo_rq01_idade, "casas": 2},
    {"titulo": "RQ02 - PRs aceitas", "coluna": "prs_aceitas", "resumo": stats.resumo_rq02_prs_aceitas, "casas": 0},
    {"titulo": "RQ03 - Releases", "coluna": "total_releases", "resumo": stats.resumo_rq03_releases, "casas": 0},
    {
        "titulo": "RQ04 - Dias desde atualização",
        "coluna": "dias_desde_atualizacao",
        "resumo": stats.resumo_rq04_atualizacao,
        "casas": 0,
    },
    {
        "titulo": "RQ06 - % issues fechadas",
        "coluna": "razao_fechadas",
        "resumo": stats.resumo_rq06_razao_fechadas,
        "casas": 2,
    },
]

st.set_page_config(page_title="Lab01 - Repositórios populares do GitHub", layout="wide")
st.title("Lab01 - Características de repositórios populares")


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


@st.cache_data
def carregar_rq07() -> pd.DataFrame | None:
    if not RQ07_PATH.exists():
        return None
    return pd.read_csv(RQ07_PATH)


def renderizar_aba_numerica(df: pd.DataFrame, coluna: str, resumo_fn, casas: int) -> None:
    resumo = resumo_fn(df)
    fmt = f"{{:.{casas}f}}"
    col_metricas, col_grafico = st.columns([1, 3])
    with col_metricas:
        st.metric("Mediana", fmt.format(resumo["mediana"]))
        st.metric("Média", fmt.format(resumo["media"]))
        st.metric("Min / Max", f"{fmt.format(resumo['min'])} / {fmt.format(resumo['max'])}")
    with col_grafico:
        st.bar_chart(df[coluna].value_counts(bins=20).sort_index())


def renderizar_aba_rq05(df: pd.DataFrame) -> None:
    resumo = stats.resumo_rq05_linguagens(df, top_n=10)
    col_metricas, col_grafico = st.columns([1, 3])
    with col_metricas:
        st.metric("Linguagens distintas", resumo["total_linguagens_distintas"])
        st.metric("Sem linguagem (N/A)", resumo["na_count"])
        st.metric("Top 10 também no Octoverse", f"{resumo['qtd_top_tambem_no_octoverse']}/10")
        st.caption(f"Fonte: GitHub Octoverse {OCTOVERSE_EDICAO} - [{OCTOVERSE_FONTE_URL}]({OCTOVERSE_FONTE_URL})")
    with col_grafico:
        st.bar_chart(resumo["contagem_top"])


def renderizar_aba_rq07(df_agrupado: pd.DataFrame | None) -> None:
    if df_agrupado is None:
        st.warning("`data/processed/rq07_resultado_agrupado.csv` não encontrado - rode `scripts/rq07_analise.py`.")
        return
    top = df_agrupado.nlargest(8, "quantidade_repos").set_index("linguagem_primaria")
    st.caption("Top 8 linguagens (por quantidade de repositórios na amostra)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("RQ02 - PRs aceitas (média)")
        st.bar_chart(top["media_prs_aceitas"])
    with col2:
        st.write("RQ03 - Releases (média)")
        st.bar_chart(top["media_releases"])
    with col3:
        st.write("RQ04 - Dias desde atualização (média)")
        st.bar_chart(top["media_dias_atualizacao"])


if not DATASET_PATH.exists():
    st.error(
        f"Dataset não encontrado em `{DATASET_PATH}`. "
        "Rode `python scripts/script_unico_s02.py` primeiro para gerar os dados."
    )
    st.stop()

df = carregar_dados()
st.caption(f"{len(df)} repositórios (top estrelas do GitHub, coleta da S02)")

nomes_abas = [aba["titulo"] for aba in ABAS_NUMERICAS] + ["RQ05 - Linguagens", "RQ07 - Combinada"]
abas = st.tabs(nomes_abas)

for aba, config in zip(abas, ABAS_NUMERICAS):
    with aba:
        renderizar_aba_numerica(df, config["coluna"], config["resumo"], config["casas"])

with abas[-2]:
    renderizar_aba_rq05(df)

with abas[-1]:
    renderizar_aba_rq07(carregar_rq07())
