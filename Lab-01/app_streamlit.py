"""
Dashboard interativo do Lab01 (Streamlit).

Reaproveita `src/analysis` - a mesma fonte de estatísticas usada pelas figuras
estáticas do relatório (`scripts/gerar_relatorio_figuras.py`), pra não duplicar
cálculo entre as duas apresentações. Cobertura atual: RQ01, RQ02 (#15). RQ03-04
(#16) e RQ05-07 (#17) entram como novas abas conforme essas Issues avançam.

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

st.set_page_config(page_title="Lab01 - Repositórios populares do GitHub", layout="wide")
st.title("Lab01 - Características de repositórios populares")


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


if not DATASET_PATH.exists():
    st.error(
        f"Dataset não encontrado em `{DATASET_PATH}`. "
        "Rode `python scripts/script_unico_s02.py` primeiro para gerar os dados."
    )
    st.stop()

df = carregar_dados()
st.caption(f"{len(df)} repositórios (top estrelas do GitHub, coleta da S02)")

aba_rq01, aba_rq02 = st.tabs(["RQ01 - Idade", "RQ02 - PRs aceitas"])

with aba_rq01:
    resumo = stats.resumo_rq01_idade(df)
    col_metricas, col_grafico = st.columns([1, 3])
    with col_metricas:
        st.metric("Mediana (anos)", f"{resumo['mediana']:.2f}")
        st.metric("Média (anos)", f"{resumo['media']:.2f}")
        st.metric("Min / Max", f"{resumo['min']:.2f} / {resumo['max']:.2f}")
    with col_grafico:
        st.bar_chart(df["idade_anos"].value_counts(bins=20).sort_index())

with aba_rq02:
    resumo = stats.resumo_rq02_prs_aceitas(df)
    col_metricas, col_grafico = st.columns([1, 3])
    with col_metricas:
        st.metric("Mediana", f"{resumo['mediana']:.0f}")
        st.metric("Média", f"{resumo['media']:.0f}")
        st.metric("Min / Max", f"{resumo['min']:.0f} / {resumo['max']:.0f}")
    with col_grafico:
        st.bar_chart(df["prs_aceitas"].value_counts(bins=20).sort_index())
