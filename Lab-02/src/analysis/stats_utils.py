"""Funções estatísticas compartilhadas por RQ1 (tempo) e RQ2 (defeitos).

Dono: Gustavo, Issues [S03] RQ1 e RQ2.

Abordagem de pareamento: o desenho do experimento não pareia trial-a-trial
(cada kata é resolvido por integrantes diferentes, em tratamentos
diferentes — ver `katas/README.md`), então o Wilcoxon pareado é aplicado
por INTEGRANTE: mediana dos 3 trials "Com IA" de cada pessoa vs. mediana dos
3 "Sem IA" da mesma pessoa, dando N=3 pares (dado o desenho within-subject
recomendado no enunciado). É pouco poder estatístico — documentar isso na
discussão do relatório, não é um bug do script.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class DescritivasPorTratamento:
    tratamento: str
    n: int
    mediana: float
    iqr: float
    minimo: float
    maximo: float


@dataclass
class ResultadoWilcoxon:
    n_pares: int
    pares: list[tuple[str, float, float]]  # (integrante ou kata, valor_com_ia, valor_sem_ia)
    estatistica: float | None
    p_valor: float | None
    erro: str | None


def descritivas_por_tratamento(df: pd.DataFrame, coluna_valor: str) -> list[DescritivasPorTratamento]:
    """Mediana e IQR por tratamento — métrica agregada recomendada pelo
    enunciado (mediana, não média, dado o N pequeno)."""
    resultado = []
    for tratamento, grupo in df.groupby("tratamento"):
        valores = grupo[coluna_valor].to_numpy(dtype=float)
        resultado.append(
            DescritivasPorTratamento(
                tratamento=tratamento,
                n=len(valores),
                mediana=float(np.median(valores)),
                iqr=float(stats.iqr(valores)) if len(valores) > 1 else 0.0,
                minimo=float(valores.min()),
                maximo=float(valores.max()),
            )
        )
    return sorted(resultado, key=lambda r: r.tratamento)


def identificar_outliers_iqr(df: pd.DataFrame, coluna_valor: str) -> pd.DataFrame:
    """Regra clássica de outlier via IQR (Q1 - 1.5*IQR, Q3 + 1.5*IQR),
    aplicada por tratamento (para não comparar tempos de com_ia contra a
    distribuição de sem_ia). Retorna só as linhas marcadas como outlier."""
    outliers = []
    for tratamento, grupo in df.groupby("tratamento"):
        valores = grupo[coluna_valor].to_numpy(dtype=float)
        if len(valores) < 4:
            continue
        q1, q3 = np.percentile(valores, [25, 75])
        iqr = q3 - q1
        limite_inferior, limite_superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (grupo[coluna_valor] < limite_inferior) | (grupo[coluna_valor] > limite_superior)
        outliers.append(grupo[mask])
    if not outliers:
        return df.iloc[0:0]
    return pd.concat(outliers)


def medianas_pareadas_por_participante(
    df: pd.DataFrame, coluna_valor: str, chave: str = "integrante"
) -> ResultadoWilcoxon:
    """Mediana por (chave, tratamento), pareando com_ia vs sem_ia da mesma
    chave, e rodando o Wilcoxon signed-rank nesses pares.

    `chave` padrão é "integrante" (RQ1/RQ2). A RQ3 também usa `chave="kata"`
    como análise complementar (N=6): métricas estruturais dependem muito do
    kata, e todo kata foi resolvido nos dois tratamentos (por integrantes
    diferentes, ver `katas/README.md`)."""
    medianas = df.groupby([chave, "tratamento"])[coluna_valor].median()

    pares: list[tuple[str, float, float]] = []
    for valor_chave in sorted(df[chave].unique()):
        try:
            valor_com_ia = float(medianas[(valor_chave, "com_ia")])
            valor_sem_ia = float(medianas[(valor_chave, "sem_ia")])
        except KeyError:
            continue  # chave sem trials nos dois tratamentos ainda
        pares.append((valor_chave, valor_com_ia, valor_sem_ia))

    if len(pares) < 2:
        return ResultadoWilcoxon(len(pares), pares, None, None, "menos de 2 pares — Wilcoxon não aplicável")

    x = [p[1] for p in pares]
    y = [p[2] for p in pares]
    try:
        # N pequeno (3 pares) faz o scipy cair no método exato; o cálculo
        # interno da aproximação normal (não usado no resultado) ainda roda
        # e emite um RuntimeWarning de divisão inválida — benigno, silenciado
        # aqui em vez de poluir a saída de quem rodar o script.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            estatistica, p_valor = stats.wilcoxon(x, y)
        return ResultadoWilcoxon(len(pares), pares, float(estatistica), float(p_valor), None)
    except ValueError as e:
        # ex.: todas as diferenças são zero, ou N pequeno demais pro método padrão
        return ResultadoWilcoxon(len(pares), pares, None, None, str(e))
