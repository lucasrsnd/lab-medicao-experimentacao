"""CFR (a) e tempo de recuperação com fixtures construídas à mão (RQ03a/RQ04)."""
from datetime import datetime, timedelta, timezone

import pytest

from lab03.domain import WorkflowRun
from lab03.metrics import calculate_ci_failure_rate, calculate_recovery

DAY = datetime(2025, 6, 10, tzinfo=timezone.utc)
_ids = iter(range(1, 10_000))


def at(hour, minute=0):
    return DAY.replace(hour=hour, minute=minute)


def run(conclusion, start, *, end=None, workflow=1, started="same", status="completed"):
    """`start` = created_at; `end` = updated_at (padrão: 1 min depois)."""
    return WorkflowRun(
        id=next(_ids), workflow_id=workflow, workflow_name=f"wf{workflow}",
        branch="main", event="push", status=status, conclusion=conclusion,
        head_sha="s", created_at=start,
        run_started_at=start if started == "same" else started,
        updated_at=end if end is not None else start + timedelta(minutes=1),
    )


# ---------------------------------------------------------------- CFR (a)

def test_cfr_2_falhas_em_8_runs():
    runs = [run("success", at(h)) for h in range(6)] + [
        run("failure", at(6)), run("timed_out", at(7)),
    ]
    result = calculate_ci_failure_rate(runs)
    assert (result.failures, result.successes, result.runs_evaluated) == (2, 6, 8)
    assert result.rate == pytest.approx(0.25)


def test_cfr_conta_failure_timed_out_e_startup_failure_como_falha():
    runs = [run(c, at(i)) for i, c in enumerate(
        ["failure", "timed_out", "startup_failure", "success"])]
    assert calculate_ci_failure_rate(runs).rate == pytest.approx(0.75)


def test_cfr_ignora_cancelled_skipped_neutral_e_em_andamento():
    runs = [
        run("success", at(1)), run("failure", at(2)),
        run("cancelled", at(3)), run("cancelled", at(4)), run("skipped", at(5)),
        run("neutral", at(6)), run("action_required", at(7)), run("stale", at(8)),
        run(None, at(9), status="in_progress"),
    ]
    result = calculate_ci_failure_rate(runs)
    assert result.rate == 0.5 and result.runs_evaluated == 2
    assert result.ignored == {
        "action_required": 1, "cancelled": 2, "in_progress_or_empty": 1,
        "neutral": 1, "skipped": 1, "stale": 1,
    }


def test_cfr_sem_runs_validos_e_none_e_nao_zero():
    result = calculate_ci_failure_rate([run("cancelled", at(1))])
    assert result.rate is None and result.runs_evaluated == 0
    assert calculate_ci_failure_rate([]).rate is None


def test_cfr_todos_sucesso_e_zero_e_todos_falha_e_um():
    assert calculate_ci_failure_rate([run("success", at(1))]).rate == 0.0
    assert calculate_ci_failure_rate([run("failure", at(1))]).rate == 1.0


def test_cfr_agrega_todos_os_workflows_juntos():
    runs = [run("failure", at(1), workflow=1), run("success", at(2), workflow=2),
            run("success", at(3), workflow=2), run("success", at(4), workflow=3)]
    assert calculate_ci_failure_rate(runs).rate == 0.25


# ------------------------------------------------------- recuperação (RQ04)

def test_exemplo_do_enunciado_recuperacao_de_1h20():
    runs = [
        run("success", at(9)),
        run("failure", at(10)),
        run("failure", at(10, 30)),
        run("success", at(11, 15), end=at(11, 20)),
    ]
    result = calculate_recovery(runs)
    assert result.episodes_total == 1 and result.censored_episodes == 0
    assert result.median_hours == pytest.approx(80 / 60)
    assert result.episodes[0].failed_runs == 2


def test_falha_nunca_recuperada_e_censurada_e_nao_descartada():
    runs = [run("success", at(9)), run("failure", at(10)), run("failure", at(12))]
    result = calculate_recovery(runs)
    assert result.episodes_total == 1 and result.censored_episodes == 1
    assert result.censored_proportion == 1.0
    assert result.median_hours is None
    assert result.episodes[0].censored and result.episodes[0].failed_runs == 2


def test_mediana_so_de_recuperados_e_proporcao_inclui_censurados():
    runs = [
        run("success", at(1)), run("failure", at(2)), run("success", at(3), end=at(4)),  # 2h
        run("failure", at(5)), run("success", at(6), end=at(9)),                          # 4h
        run("failure", at(10)),                                                            # censurado
    ]
    result = calculate_recovery(runs)
    assert result.episodes_total == 3 and result.episodes_recovered == 2
    assert result.median_hours == pytest.approx(3.0)
    assert result.censored_proportion == pytest.approx(1 / 3)


def test_cancelled_nao_encerra_nem_abre_episodio():
    runs = [
        run("success", at(1)), run("failure", at(2)),
        run("cancelled", at(3)), run("skipped", at(4)),
        run("success", at(5), end=at(5, 30)),
    ]
    result = calculate_recovery(runs)
    assert result.episodes_total == 1
    assert result.median_hours == pytest.approx(3.5)
    only_cancelled = calculate_recovery([run("success", at(1)), run("cancelled", at(2))])
    assert only_cancelled.episodes_total == 0 and only_cancelled.median_hours is None


def test_workflows_sao_independentes():
    runs = [
        run("success", at(1), workflow=1), run("failure", at(2), workflow=1),
        run("success", at(2, 10), workflow=2),  # sucesso de OUTRO workflow não recupera
        run("success", at(4), end=at(4), workflow=1),
        run("success", at(1), workflow=2), run("failure", at(3), workflow=2),
    ]
    result = calculate_recovery(runs)
    by_workflow = {e.workflow_id: e for e in result.episodes}
    assert by_workflow[1].recovery_hours == pytest.approx(2.0)
    assert by_workflow[2].censored
    assert result.episodes_total == 2


def test_mediana_agrega_episodios_de_todos_os_workflows():
    runs = [
        run("success", at(1), workflow=1), run("failure", at(2), workflow=1),
        run("success", at(3), end=at(3), workflow=1),            # 1h
        run("success", at(1), workflow=2), run("failure", at(2), workflow=2),
        run("success", at(6), end=at(6), workflow=2),            # 4h
        run("success", at(1), workflow=3), run("failure", at(2), workflow=3),
        run("success", at(10), end=at(10), workflow=3),          # 8h
    ]
    assert calculate_recovery(runs).median_hours == pytest.approx(4.0)


def test_falhas_iniciais_sem_sucesso_anterior_nao_abrem_episodio():
    runs = [run("failure", at(1)), run("failure", at(2)), run("success", at(3))]
    result = calculate_recovery(runs)
    assert result.episodes_total == 0
    assert result.leading_failures_without_prior_success == 2


def test_usa_run_started_at_da_primeira_falha_e_updated_at_do_sucesso():
    runs = [
        run("success", at(1)),
        run("failure", at(10, 5), started=at(10)),  # criado 10:05, iniciou 10:00
        run("success", at(11), end=at(11, 20)),
    ]
    assert calculate_recovery(runs).median_hours == pytest.approx(80 / 60)


def test_run_started_at_ausente_usa_created_at():
    runs = [run("success", at(1)), run("failure", at(2), started=None),
            run("success", at(3), end=at(3))]
    assert calculate_recovery(runs).median_hours == pytest.approx(1.0)


def test_ordem_de_entrada_nao_importa():
    ordered = [run("success", at(1)), run("failure", at(2)),
               run("success", at(3), end=at(3))]
    assert calculate_recovery(reversed(ordered)).median_hours == pytest.approx(1.0)


def test_updated_at_anterior_ao_inicio_e_excluido_e_contado():
    runs = [run("success", at(1)), run("failure", at(5)), run("success", at(6), end=at(4))]
    result = calculate_recovery(runs)
    assert result.episodes_total == 0
    assert result.exclusions == {"invalid_recovery_timestamps": 1}


def test_sem_runs_ou_so_sucessos_nao_gera_episodios():
    for runs in ([], [run("success", at(1)), run("success", at(2))]):
        result = calculate_recovery(runs)
        assert result.episodes_total == 0
        assert result.median_hours is None and result.censored_proportion is None
