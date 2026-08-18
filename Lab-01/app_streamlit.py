"""
Dashboard interativo do Lab01 (Streamlit).

Reaproveita `src/analysis` - a mesma fonte de estatísticas usada pelas figuras
estáticas do relatório (`scripts/gerar_relatorio_figuras.py`), pra não duplicar
cálculo entre as duas apresentações. Cobertura atual: RQ01-RQ04 (#15, #16).
RQ05-07 (#17) entram como novas abas conforme essa Issue avança.

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

DATASET_PATH = Path(__file__).resolve().parent / "data" / "raw" / "repositorios_s02.csv"

# Uma entrada por RQ numérica (histograma). RQ05/RQ07 têm formato diferente
# (categórico/agrupado) e entram à parte quando chegar a #17.
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
]

st.set_page_config(page_title="Lab01 - Repositórios populares do GitHub", layout="wide")
st.title("Lab01 - Características de repositórios populares")


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


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


if not DATASET_PATH.exists():
    st.error(
        f"Dataset não encontrado em `{DATASET_PATH}`. "
        "Rode `python scripts/script_unico_s02.py` primeiro para gerar os dados."
    )
    st.stop()

df = carregar_dados()
st.caption(f"{len(df)} repositórios (top estrelas do GitHub, coleta da S02)")

abas = st.tabs([aba["titulo"] for aba in ABAS_NUMERICAS])
for aba, config in zip(abas, ABAS_NUMERICAS):
    with aba:
        renderizar_aba_numerica(df, config["coluna"], config["resumo"], config["casas"])
