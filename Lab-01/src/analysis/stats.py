"""Estatísticas descritivas por RQ, a partir do dataset coletado
(`data/raw/repositorios_s02.csv`). Funções puras (recebem um `DataFrame`, devolvem
números/dicts) - sem I/O, reaproveitadas tanto pela geração de figuras estáticas
quanto pelo dashboard Streamlit.
"""

from __future__ import annotations

import pandas as pd


def _resumo_numerico(serie: pd.Series) -> dict:
    return {
        "mediana": serie.median(),
        "media": serie.mean(),
        "min": serie.min(),
        "max": serie.max(),
        "nulos": int(serie.isna().sum()),
    }


def resumo_rq01_idade(df: pd.DataFrame) -> dict:
    """RQ01 - idade do repositório (anos)."""
    return _resumo_numerico(df["idade_anos"])


def resumo_rq02_prs_aceitas(df: pd.DataFrame) -> dict:
    """RQ02 - total de PRs aceitas (merged)."""
    return _resumo_numerico(df["prs_aceitas"])


def resumo_rq03_releases(df: pd.DataFrame) -> dict:
    """RQ03 - total de releases."""
    return _resumo_numerico(df["total_releases"])


def resumo_rq04_atualizacao(df: pd.DataFrame) -> dict:
    """RQ04 - dias desde a última atualização (pushedAt)."""
    return _resumo_numerico(df["dias_desde_atualizacao"])
