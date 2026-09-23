"""Testes de src/security/bandit_scan.py.

Inclui um controle positivo (arquivo deliberadamente vulnerável) — essencial
aqui porque o resultado real do scan nos 18 trials é 0 achados em ambos os
tratamentos (ver docs/resultados-seguranca.md); sem provar que o scanner
detecta algo quando existe, um "0" poderia ser o scanner quebrado, não um
resultado real."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.security.bandit_scan import (  # noqa: E402
    CSV_FIELDS,
    gravar_csv,
    scan_arquivo,
    scan_todos_os_trials,
)


def test_scan_arquivo_detecta_vulnerabilidade_conhecida(tmp_path):
    # B307: uso de eval() é um achado clássico e estável do Bandit
    arquivo = tmp_path / "vulneravel.py"
    arquivo.write_text("def f(x):\n    return eval(x)\n", encoding="utf-8")

    totais = scan_arquivo(arquivo)

    assert totais["SEVERITY.MEDIUM"] + totais["SEVERITY.LOW"] + totais["SEVERITY.HIGH"] >= 1


def test_scan_arquivo_nao_acusa_nada_em_codigo_limpo(tmp_path):
    arquivo = tmp_path / "limpo.py"
    arquivo.write_text("def soma(a, b):\n    return a + b\n", encoding="utf-8")

    totais = scan_arquivo(arquivo)

    assert totais["SEVERITY.LOW"] + totais["SEVERITY.MEDIUM"] + totais["SEVERITY.HIGH"] == 0


def test_scan_todos_os_trials_cobre_os_18_e_grava_csv(tmp_path):
    resultados = scan_todos_os_trials()
    assert len(resultados) == 18
    assert {r.tratamento for r in resultados} == {"com_ia", "sem_ia"}
    assert {r.integrante for r in resultados} == {"gustavoprehl", "lucasrsnd", "DaviSantos23"}

    saida = tmp_path / "trials_seguranca.csv"
    gravar_csv(resultados, out_csv=saida)

    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert linhas[0] == ",".join(CSV_FIELDS)
    assert len(linhas) == 19  # cabeçalho + 18 trials
