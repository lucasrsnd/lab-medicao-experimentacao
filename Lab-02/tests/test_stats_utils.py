"""Testes unitários de src/analysis/stats_utils.py — dados sintéticos, sem
tocar nos CSVs reais."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.stats_utils import (  # noqa: E402
    descritivas_por_tratamento,
    identificar_outliers_iqr,
    medianas_pareadas_por_participante,
)


def _df(rows):
    return pd.DataFrame(rows, columns=["kata", "integrante", "tratamento", "valor"])


def test_descritivas_por_tratamento_mediana_e_iqr():
    df = _df(
        [
            ("k1", "a", "com_ia", 10.0),
            ("k2", "a", "com_ia", 20.0),
            ("k3", "a", "com_ia", 30.0),
            ("k4", "a", "sem_ia", 100.0),
            ("k5", "a", "sem_ia", 200.0),
        ]
    )
    resultado = {d.tratamento: d for d in descritivas_por_tratamento(df, "valor")}

    assert resultado["com_ia"].n == 3
    assert resultado["com_ia"].mediana == 20.0
    assert resultado["sem_ia"].mediana == 150.0


def test_identificar_outliers_iqr_marca_ponto_fora_da_faixa():
    # 4 valores próximos + 1 bem fora, mesmo tratamento (mínimo de 4 p/ regra IQR ativar)
    df = _df(
        [
            ("k1", "a", "com_ia", 10.0),
            ("k2", "a", "com_ia", 11.0),
            ("k3", "a", "com_ia", 12.0),
            ("k4", "a", "com_ia", 13.0),
            ("k5", "a", "com_ia", 1000.0),  # outlier
        ]
    )
    outliers = identificar_outliers_iqr(df, "valor")

    assert len(outliers) == 1
    assert outliers.iloc[0]["kata"] == "k5"


def test_identificar_outliers_iqr_nao_compara_entre_tratamentos_diferentes():
    # sem_ia tem só 1 ponto, bem distante de com_ia — não deve ser marcado,
    # porque outliers são calculados dentro do próprio tratamento (N<4 pula)
    df = _df(
        [
            ("k1", "a", "com_ia", 10.0),
            ("k2", "a", "com_ia", 11.0),
            ("k3", "a", "com_ia", 12.0),
            ("k4", "a", "com_ia", 13.0),
            ("k5", "a", "sem_ia", 1000.0),
        ]
    )
    outliers = identificar_outliers_iqr(df, "valor")
    assert len(outliers) == 0


def test_medianas_pareadas_por_participante_pareia_com_ia_e_sem_ia():
    df = _df(
        [
            ("k1", "gustavo", "com_ia", 10.0),
            ("k2", "gustavo", "com_ia", 20.0),
            ("k3", "gustavo", "com_ia", 30.0),
            ("k4", "gustavo", "sem_ia", 40.0),
            ("k5", "gustavo", "sem_ia", 50.0),
            ("k6", "gustavo", "sem_ia", 60.0),
            ("k1", "lucas", "com_ia", 5.0),
            ("k2", "lucas", "com_ia", 15.0),
            ("k3", "lucas", "com_ia", 25.0),
            ("k4", "lucas", "sem_ia", 100.0),
            ("k5", "lucas", "sem_ia", 110.0),
            ("k6", "lucas", "sem_ia", 120.0),
        ]
    )
    resultado = medianas_pareadas_por_participante(df, "valor")

    assert resultado.n_pares == 2
    pares = {p[0]: (p[1], p[2]) for p in resultado.pares}
    assert pares["gustavo"] == (20.0, 50.0)
    assert pares["lucas"] == (15.0, 110.0)
    assert resultado.erro is None
    assert resultado.p_valor is not None


def test_medianas_pareadas_ignora_integrante_sem_os_dois_tratamentos():
    df = _df(
        [
            ("k1", "gustavo", "com_ia", 10.0),
            ("k4", "gustavo", "sem_ia", 40.0),
            ("k1", "davi", "com_ia", 5.0),  # davi não tem trial sem_ia aqui
        ]
    )
    resultado = medianas_pareadas_por_participante(df, "valor")

    # só 1 par válido (gustavo) -> Wilcoxon não aplicável (precisa de 2+)
    assert resultado.n_pares == 1
    assert resultado.erro is not None


def test_medianas_pareadas_por_kata_pareia_trials_de_integrantes_diferentes():
    df = _df(
        [
            ("k1", "gustavo", "com_ia", 4.0),
            ("k1", "davi", "com_ia", 6.0),
            ("k1", "lucas", "sem_ia", 11.0),
            ("k2", "gustavo", "com_ia", 5.0),
            ("k2", "lucas", "sem_ia", 3.0),
            ("k2", "davi", "sem_ia", 3.0),
        ]
    )
    resultado = medianas_pareadas_por_participante(df, "valor", chave="kata")

    assert resultado.n_pares == 2
    assert resultado.pares == [("k1", 5.0, 11.0), ("k2", 5.0, 3.0)]
