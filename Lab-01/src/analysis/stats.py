"""Estatísticas descritivas por RQ, a partir do dataset coletado
(`data/raw/repositorios_s02.csv`). Funções puras (recebem um `DataFrame`, devolvem
números/dicts) - sem I/O, reaproveitadas tanto pela geração de figuras estáticas
quanto pelo dashboard Streamlit.
"""

from __future__ import annotations

import pandas as pd


def resumo_rq01_idade(df: pd.DataFrame) -> dict:
    """RQ01 - idade do repositório (anos)."""
    serie = df["idade_anos"]
    return {
        "mediana": serie.median(),
        "media": serie.mean(),
        "min": serie.min(),
        "max": serie.max(),
        "nulos": int(serie.isna().sum()),
    }


def resumo_rq02_prs_aceitas(df: pd.DataFrame) -> dict:
    """RQ02 - total de PRs aceitas (merged)."""
    serie = df["prs_aceitas"]
    return {
        "mediana": serie.median(),
        "media": serie.mean(),
        "min": serie.min(),
        "max": serie.max(),
        "nulos": int(serie.isna().sum()),
    }
