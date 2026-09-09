"""Testes unitários de src/metrics/static_metrics.py.

Radon é chamado de verdade (é puro Python, rápido, sem I/O externo). `jscpd`
depende de `npx`/Node, então é substituído por um fake injetado via
`jscpd_fn`, mesma técnica de injeção de `src.timing.trial_timer`
(clock/sleep/runner fakes), sem depender de rede/Node para rodar a suíte.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metrics.static_metrics import (  # noqa: E402
    DuplicationMetrics,
    append_result,
    collect_static_metrics,
    find_source_files,
)

FAKE_DUPLICATION = DuplicationMetrics(
    linhas_totais=10, linhas_duplicadas=0, duplicacao_pct=0.0, clones=0
)


def _fake_jscpd(_path: Path) -> DuplicationMetrics:
    return FAKE_DUPLICATION


def test_find_source_files_ignora_testes_e_conftest(tmp_path: Path) -> None:
    (tmp_path / "solution.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "test_solution.py").write_text("def test_f():\n    assert True\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")

    arquivos = find_source_files(tmp_path)

    assert [a.name for a in arquivos] == ["solution.py"]


def test_find_source_files_aceita_arquivo_unico(tmp_path: Path) -> None:
    arquivo = tmp_path / "solution.py"
    arquivo.write_text("x = 1\n", encoding="utf-8")

    assert find_source_files(arquivo) == [arquivo]


def test_find_source_files_sem_solucao_encerra(tmp_path: Path) -> None:
    (tmp_path / "test_solution.py").write_text("", encoding="utf-8")

    with __import__("pytest").raises(SystemExit):
        find_source_files(tmp_path)


def test_collect_static_metrics_conta_complexidade_e_loc(tmp_path: Path) -> None:
    codigo = (
        "def f(x):\n"
        "    if x > 0:\n"
        "        return 1\n"
        "    return 0\n"
    )
    (tmp_path / "solution.py").write_text(codigo, encoding="utf-8")

    resultado = collect_static_metrics(
        kata="k1", integrante="lucasrsnd", tratamento="sem_ia", path=tmp_path, jscpd_fn=_fake_jscpd
    )

    assert resultado.arquivos_analisados == 1
    assert resultado.num_blocos == 1  # uma função
    assert resultado.complexidade_total == 2  # if simples -> cc=2
    assert resultado.sloc == 4
    assert resultado.erro_parse is False
    assert resultado.duplicacao_pct == 0.0


def test_collect_static_metrics_registra_erro_de_sintaxe_sem_derrubar(tmp_path: Path) -> None:
    (tmp_path / "solution.py").write_text("def f(:\n    pass\n", encoding="utf-8")

    resultado = collect_static_metrics(
        kata="k1", integrante="lucasrsnd", tratamento="com_ia", path=tmp_path, jscpd_fn=_fake_jscpd
    )

    assert resultado.erro_parse is True
    assert resultado.complexidade_total == 0
    assert resultado.sloc == 0


def test_collect_static_metrics_arquivo_vazio_nao_e_erro(tmp_path: Path) -> None:
    (tmp_path / "solution.py").write_text("", encoding="utf-8")

    resultado = collect_static_metrics(
        kata="k1", integrante="lucasrsnd", tratamento="sem_ia", path=tmp_path, jscpd_fn=_fake_jscpd
    )

    assert resultado.erro_parse is False
    assert resultado.sloc == 0
    assert resultado.mi == 100.0


def test_append_result_cria_csv_com_cabecalho(tmp_path: Path) -> None:
    (tmp_path / "solution.py").write_text("x = 1\n", encoding="utf-8")
    resultado = collect_static_metrics(
        kata="k1", integrante="lucasrsnd", tratamento="sem_ia", path=tmp_path, jscpd_fn=_fake_jscpd
    )

    csv_path = tmp_path / "saida" / "trials_metricas.csv"
    append_result(resultado, csv_path=csv_path)
    append_result(resultado, csv_path=csv_path)

    linhas = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert linhas[0].startswith("kata,integrante,tratamento")
    assert len(linhas) == 3  # cabeçalho + 2 linhas
