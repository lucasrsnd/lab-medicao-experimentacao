"""Testes unitários de src/timing/trial_timer.py.

Não esperam tempo real: clock/sleep/runner são fakes injetados, então mesmo o
caso de censura em 35 min roda instantaneamente.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.timing.trial_timer import (  # noqa: E402
    PytestSummary,
    append_result,
    poll_until_green,
)


class FakeClock:
    """Avança `step` segundos a cada chamada de sleep; clock() lê o acumulado."""

    def __init__(self, step: float) -> None:
        self.now = 0.0
        self.step = step

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += self.step


def _runner_sequence(*summaries: PytestSummary):
    """Retorna um runner fake que devolve `summaries` em sequência e repete o
    último valor indefinidamente depois disso (simula testes que continuam
    falhando até o time-box)."""
    it = iter(summaries)
    last = summaries[-1]

    def runner(_test_path):
        nonlocal last
        try:
            last = next(it)
        except StopIteration:
            pass
        return last

    return runner


def test_time_to_green_para_no_primeiro_poll_com_sucesso():
    fake = FakeClock(step=10)  # poll_interval do teste
    result = poll_until_green(
        kata="k1",
        integrante="gustavoprehl",
        tratamento="com_ia",
        test_path=Path("katas/k1/com_ia/gustavoprehl"),
        timebox_min=35,
        poll_interval_sec=10,
        runner=_runner_sequence(PytestSummary(passed=3, failed=0, errors=0)),
        clock=fake.clock,
        sleep_fn=fake.sleep,
    )

    assert result.censurado is False
    assert result.testes_passando == 3
    assert result.testes_total == 3
    assert result.tempo_min == 0.0  # verde já no 1º poll, antes de qualquer sleep


def test_registra_time_to_green_apos_alguns_polls_com_falha():
    fake = FakeClock(step=10)
    result = poll_until_green(
        kata="k1",
        integrante="gustavoprehl",
        tratamento="sem_ia",
        test_path=Path("katas/k1/sem_ia/gustavoprehl"),
        timebox_min=35,
        poll_interval_sec=10,
        runner=_runner_sequence(
            PytestSummary(passed=1, failed=2, errors=0),
            PytestSummary(passed=2, failed=1, errors=0),
            PytestSummary(passed=3, failed=0, errors=0),
        ),
        clock=fake.clock,
        sleep_fn=fake.sleep,
    )

    assert result.censurado is False
    # 2 sleeps de 10s até o poll que veio verde (3º runner call)
    assert result.tempo_min == round(20 / 60, 2)
    assert result.testes_passando == 3


def test_censura_no_timebox_sem_descartar_o_trial():
    fake = FakeClock(step=60)  # 1 min por poll
    result = poll_until_green(
        kata="k2",
        integrante="gustavoprehl",
        tratamento="com_ia",
        test_path=Path("katas/k2/com_ia/gustavoprehl"),
        timebox_min=5,  # time-box curto só pra não precisar de 35 iterações no teste
        poll_interval_sec=60,
        runner=_runner_sequence(PytestSummary(passed=1, failed=1, errors=0)),
        clock=fake.clock,
        sleep_fn=fake.sleep,
    )

    assert result.censurado is True
    assert result.tempo_min == 5.0  # grava o time-box inteiro, não o tempo parcial
    # RQ2 precisa do nº de testes passando mesmo em censura:
    assert result.testes_passando == 1
    assert result.testes_total == 2


def test_append_result_cria_cabecalho_na_primeira_escrita(tmp_path):
    fake = FakeClock(step=10)
    result = poll_until_green(
        kata="k1",
        integrante="lucasrsnd",
        tratamento="com_ia",
        test_path=Path("katas/k1/com_ia/lucasrsnd"),
        timebox_min=35,
        poll_interval_sec=10,
        runner=_runner_sequence(PytestSummary(passed=1, failed=0, errors=0)),
        clock=fake.clock,
        sleep_fn=fake.sleep,
    )

    csv_path = tmp_path / "trials_tempo.csv"
    append_result(result, csv_path=csv_path)
    append_result(result, csv_path=csv_path)  # 2ª chamada não deve duplicar o cabeçalho

    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("timestamp_inicio,")
    assert len(linhas) == 3  # cabeçalho + 2 trials
