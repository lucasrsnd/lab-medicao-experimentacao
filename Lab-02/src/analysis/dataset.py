"""Carregamento compartilhado dos dados brutos da S02 (`data/raw/`) para as
análises de RQ1/RQ2/RQ3 da S03.

Dono: Gustavo, Issues [S03] RQ1 (tempo) e RQ2 (defeitos). O `src/metrics/`
(Lucas, RQ3) tem seu próprio consumo de `trials_metricas.csv`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import pandas as pd

LAB02_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = LAB02_ROOT / "data" / "raw"

TRIALS_TEMPO_CSV = RAW_DIR / "trials_tempo.csv"
TRIALS_METRICAS_CSV = RAW_DIR / "trials_metricas.csv"


class KnownIssue(TypedDict):
    kata: str
    integrante: str
    tratamento: str
    motivo: str
    recomendacao: str


# Problemas de instrumentação (não de dificuldade real da tarefa) já
# identificados nos dados brutos. Sinalizados, não removidos silenciosamente
# — a decisão de excluir/re-rodar é do grupo (ver commit 9a79389).
KNOWN_DATA_ISSUES: list[KnownIssue] = [
    {
        "kata": "k2",
        "integrante": "DaviSantos23",
        "tratamento": "sem_ia",
        "motivo": (
            "Registrado como censurado (35min, 0/2 testes) por conflito de "
            "import do pytest — os conftest.py de proteção contra colisão de "
            "módulo (ver katas/kX/.../conftest.py) foram removidos antes "
            "desse trial rodar. Rodando o mesmo código isoladamente após a "
            "correção (commit 9a79389), passa 3/3."
        ),
        "recomendacao": "excluir_ou_rerodar",
    },
]


def load_trials_tempo() -> pd.DataFrame:
    """Carrega `data/raw/trials_tempo.csv` (RQ1) e marca outliers de
    instrumentação conhecidos numa coluna `possivel_outlier_instrumentacao`."""
    df = pd.read_csv(TRIALS_TEMPO_CSV)
    return _flag_known_issues(df)


def load_trials_metricas() -> pd.DataFrame:
    """Carrega `data/raw/trials_metricas.csv` (RQ2 usa testes_passando/total
    de lá também, via trials_tempo; este arquivo é mais usado pela RQ3)."""
    df = pd.read_csv(TRIALS_METRICAS_CSV)
    return _flag_known_issues(df)


def _flag_known_issues(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["possivel_outlier_instrumentacao"] = False
    for issue in KNOWN_DATA_ISSUES:
        mask = (
            (df["kata"] == issue["kata"])
            & (df["integrante"] == issue["integrante"])
            & (df["tratamento"] == issue["tratamento"])
        )
        df.loc[mask, "possivel_outlier_instrumentacao"] = True
    return df


def split_scenarios(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Retorna os dois cenários de análise: com todos os trials, e excluindo
    os sinalizados como outlier de instrumentação — ambos são calculados
    porque a decisão de qual usar é do grupo, não do script."""
    return {
        "todos_os_trials": df,
        "excluindo_outliers_instrumentacao": df[~df["possivel_outlier_instrumentacao"]],
    }
