"""Estatísticas descritivas por RQ, a partir do dataset coletado
(`data/raw/repositorios_s02.csv`). Funções puras (recebem um `DataFrame`, devolvem
números/dicts) - sem I/O, reaproveitadas tanto pela geração de figuras estáticas
quanto pelo dashboard Streamlit.
"""

from __future__ import annotations

import pandas as pd

from src.analysis.referencias import OCTOVERSE_TOP_LINGUAGENS


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


def resumo_rq05_linguagens(df: pd.DataFrame, top_n: int = 10) -> dict:
    """RQ05 - contagem por linguagem primária + comparação com o ranking do
    GitHub Octoverse (`src.analysis.referencias`), única fonte usada no laboratório
    inteiro para "linguagens mais populares"."""
    contagem = df["linguagem_primaria"].value_counts()
    top = contagem.head(top_n)
    no_octoverse = [lang for lang in top.index if lang in OCTOVERSE_TOP_LINGUAGENS]
    return {
        "contagem_top": top,
        "total_linguagens_distintas": df["linguagem_primaria"].nunique(),
        "na_count": int((df["linguagem_primaria"] == "N/A").sum()),
        "qtd_top_tambem_no_octoverse": len(no_octoverse),
        "linguagens_top_tambem_no_octoverse": no_octoverse,
    }


def resumo_rq06_razao_fechadas(df: pd.DataFrame) -> dict:
    """RQ06 - razão entre issues fechadas e total de issues."""
    return _resumo_numerico(df["razao_fechadas"])
