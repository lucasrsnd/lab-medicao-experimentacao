from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from lab03.collectors.workflow_runs import collect_workflow_runs, month_slices
from lab03.domain import Window, timestamp
from lab03.github import DataError, GitHubClient, Response

VALID = ("success", "failure", "timed_out", "startup_failure")
WINDOW = Window(timestamp("2025-01-01T00:00:00Z"), timestamp("2026-01-01T00:00:00Z"))


def raw_run(run_id, created, conclusion="success", **overrides):
    run = {
        "id": run_id, "workflow_id": 1, "name": "CI", "head_branch": "main",
        "event": "push", "status": "completed", "conclusion": conclusion,
        "head_sha": f"sha{run_id}", "created_at": created,
        "run_started_at": created, "updated_at": created,
    }
    run.update(overrides)
    return run


class RunsApi:
    """Simula /actions/runs: filtro `created` inclusivo, teto de 1.000 e paginação."""

    def __init__(self, runs, per_page_cap=1000):
        self.runs = runs
        self.cap = per_page_cap
        self.queries = []

    def get(self, url):
        params = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        low, high = (timestamp(v) for v in params["created"].split(".."))
        self.queries.append((low, high))
        matched = [r for r in self.runs if low <= timestamp(r["created_at"]) <= high]
        page = int(params.get("page", 1))
        size = int(params["per_page"])
        reachable = matched[: self.cap]
        chunk = reachable[(page - 1) * size: page * size]
        headers = {}
        if page * size < len(reachable):
            headers["link"] = f'<{url.split("&page=")[0]}&page={page + 1}>; rel="next"'
        return Response({"total_count": len(matched), "workflow_runs": chunk}, headers)


def collect(api, window=WINDOW):
    stats = {}
    runs = collect_workflow_runs(GitHubClient(api), "o/r", window, "main", VALID, stats=stats)
    return runs, stats


def test_month_slices_cobrem_a_janela_sem_lacunas_nem_sobreposicao():
    window = Window(timestamp("2025-10-06T03:00:00Z"), timestamp("2026-10-07T02:59:59Z"))
    slices = month_slices(window)
    assert len(slices) == 13
    assert slices[0].start == window.start and slices[-1].end == window.end
    assert all(a.end == b.start for a, b in zip(slices, slices[1:]))
    assert slices[1].start == timestamp("2025-11-01T00:00:00Z")


def test_janela_com_fuso_e_normalizada_para_utc():
    window = Window(timestamp("2025-10-06T00:00:00-03:00"), timestamp("2025-12-01T00:00:00-03:00"))
    slices = month_slices(window)
    assert slices[0].start == timestamp("2025-10-06T03:00:00Z")
    assert slices[-1].end == timestamp("2025-12-01T03:00:00Z")


def test_coleta_em_fatias_mensais_sem_duplicar_nem_perder():
    runs = [raw_run(i, f"2025-{(i % 12) + 1:02d}-15T10:00:00Z") for i in range(1, 121)]
    result, stats = collect(RunsApi(runs))
    assert list(result) == sorted(result, key=lambda r: (r.created_at, r.id))
    assert {r.id for r in result} == set(range(1, 121))
    assert stats["slices"] == 12 and stats["bisections"] == 0


def test_run_exatamente_na_fronteira_entre_meses_aparece_uma_vez():
    runs = [raw_run(1, "2025-03-01T00:00:00Z"), raw_run(2, "2025-02-28T23:59:59Z")]
    result, _ = collect(RunsApi(runs))
    assert sorted(r.id for r in result) == [1, 2]


def test_fim_da_janela_e_exclusivo():
    runs = [raw_run(1, "2025-12-31T23:59:59Z"), raw_run(2, "2026-01-01T00:00:00Z")]
    result, _ = collect(RunsApi(runs))
    assert [r.id for r in result] == [1]


def test_mes_acima_do_teto_e_subdividido_sem_truncar():
    start = datetime(2025, 5, 1, tzinfo=timezone.utc)
    runs = [
        raw_run(i, (start + timedelta(minutes=20 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for i in range(1, 1501)
    ]
    api = RunsApi(runs)
    result, stats = collect(api)
    assert len(result) == 1500
    assert stats["bisections"] >= 1


def test_mes_exatamente_no_teto_nao_precisa_de_subdivisao():
    start = datetime(2025, 5, 1, tzinfo=timezone.utc)
    runs = [
        raw_run(i, (start + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for i in range(1, 1001)
    ]
    result, stats = collect(RunsApi(runs))
    assert len(result) == 1000 and stats["bisections"] == 0


def test_teto_nao_subdividivel_falha_em_vez_de_truncar():
    runs = [raw_run(i, "2025-05-10T10:00:00Z") for i in range(1, 1201)]
    with pytest.raises(DataError, match="subdividida"):
        collect(RunsApi(runs))


def test_paginacao_incompleta_falha():
    runs = [raw_run(i, "2025-05-10T10:00:00Z") for i in range(1, 11)]
    api = RunsApi(runs, per_page_cap=5)  # total_count=10, mas só 5 alcançáveis
    with pytest.raises(DataError, match="incompleta"):
        collect(api)


def test_filtra_conclusoes_ignoradas_branch_e_evento():
    runs = [
        raw_run(1, "2025-02-01T00:00:00Z", "success"),
        raw_run(2, "2025-02-01T01:00:00Z", "cancelled"),
        raw_run(3, "2025-02-01T02:00:00Z", None, status="in_progress"),
        raw_run(4, "2025-02-01T03:00:00Z", "failure", head_branch="dev"),
        raw_run(5, "2025-02-01T04:00:00Z", "success", event="schedule"),
        raw_run(6, "2025-02-01T05:00:00Z", "timed_out"),
    ]
    result, _ = collect(RunsApi(runs))
    assert [r.id for r in result] == [1, 6]


@pytest.mark.parametrize("payload", [[], {"workflow_runs": []}, {"total_count": -1, "workflow_runs": []}])
def test_resposta_invalida_falha(payload):
    class Bad:
        def get(self, url):
            return Response(payload, {})
    with pytest.raises(DataError):
        collect(Bad())
