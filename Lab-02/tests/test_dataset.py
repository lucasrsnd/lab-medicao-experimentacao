"""Testes de src/analysis/dataset.py contra os CSVs reais em data/raw/ — só
leitura, não escreve nada."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.dataset import KNOWN_DATA_ISSUES, load_trials_tempo, split_scenarios  # noqa: E402


def test_load_trials_tempo_tem_os_18_trials_e_as_3_pessoas():
    df = load_trials_tempo()

    assert len(df) == 18
    assert set(df["integrante"].unique()) == {"gustavoprehl", "lucasrsnd", "DaviSantos23"}
    assert set(df["tratamento"].unique()) == {"com_ia", "sem_ia"}


def test_known_issue_do_davi_k2_fica_sinalizado():
    df = load_trials_tempo()
    issue = KNOWN_DATA_ISSUES[0]

    linha = df[
        (df["kata"] == issue["kata"])
        & (df["integrante"] == issue["integrante"])
        & (df["tratamento"] == issue["tratamento"])
    ]

    assert len(linha) == 1
    assert bool(linha.iloc[0]["possivel_outlier_instrumentacao"]) is True


def test_split_scenarios_exclui_outlier_conhecido_no_segundo_cenario():
    df = load_trials_tempo()
    cenarios = split_scenarios(df)

    assert len(cenarios["todos_os_trials"]) == 18
    assert len(cenarios["excluindo_outliers_instrumentacao"]) == 17
    assert not cenarios["excluindo_outliers_instrumentacao"]["possivel_outlier_instrumentacao"].any()
