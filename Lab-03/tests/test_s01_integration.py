"""Regressões das fronteiras entre os módulos integrados na S01."""
import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from lab03.cache import SQLiteCacheTransport
from lab03.cli import main
from lab03.collectors.candidates import select_candidates
from lab03.configuration import load_config
from lab03.domain import Window, timestamp
from lab03.github import DataError, GitHubClient, Response
from lab03.metrics import calculate_recovery
from test_candidates import CandidateTransport
from test_ci_metrics import run, at
from test_pilot import PilotTransport
from test_workflow_runs import RunsApi, raw_run, collect

STUDY = Path(__file__).parents[1] / "config/estudo.json"


def selection(transport):
    return select_candidates(
        GitHubClient(transport), timestamp("2025-01-01T00:00:00Z"),
        timestamp("2026-01-01T00:00:00Z"), stars_min_exclusive=1000,
        sample_size=1, minimum_releases=1, minimum_valid_runs=1,
        valid_conclusions=("success", "failure", "timed_out", "startup_failure"),
    )


def test_selecao_usa_mesmo_coletor_sem_teto_de_mil_runs():
    class ManyRuns(CandidateTransport):
        def __init__(self):
            super().__init__()
            base = timestamp("2025-06-01T00:00:00Z")
            self.api = RunsApi([
                raw_run(i, (base + timedelta(minutes=i*20)).isoformat())
                for i in range(1500)
            ])
        def get(self, url):
            if "/actions/runs?" in url:
                return self.api.get(url)
            return super().get(url)
    result = selection(ManyRuns())
    assert result["eligible_repositories"][0]["valid_workflow_run_count"] == 1500


def test_selecao_nao_aceita_release_de_outro_branch():
    class OtherBranch(CandidateTransport):
        def get(self, url):
            if "/compare/" in url:
                return Response({"status": "diverged"}, {})
            return super().get(url)
    result = selection(OtherBranch())
    assert not result["eligible_repositories"]
    assert result["funnel"]["releases"]["excluded"] == {"minimum_releases_not_met": 1}


def test_erro_de_paginacao_de_contribuidores_nao_vira_exclusao():
    class Truncated(CandidateTransport):
        def get(self, url):
            if "/contributors?" in url:
                raise DataError("paginação incompleta")
            return super().get(url)
    with pytest.raises(DataError, match="incompleta"):
        selection(Truncated())


@pytest.mark.parametrize("end", [at(4), at(5)])
def test_sucesso_no_fim_ou_depois_da_janela_nao_recupera(end):
    window = Window(at(0), at(4))
    result = calculate_recovery([
        run("success", at(1)), run("failure", at(2)), run("success", at(3), end=end),
    ], window)
    assert result.median_hours is None
    assert result.censored_episodes == 1
    assert result.episodes[0].censored_at == at(4)


@pytest.mark.parametrize("started", [at(0), at(5)])
def test_inicio_de_falha_fora_da_janela_excluido(started):
    window = Window(at(1), at(4))
    result = calculate_recovery([
        run("success", at(1)), run("failure", at(2), started=started),
        run("success", at(3)),
    ], window)
    assert result.episodes_total == 0
    assert result.exclusions == {"failure_started_outside_window": 1}


def test_falha_aberta_sem_data_nao_recebe_inicio_inventado():
    result = calculate_recovery([run("success", at(1)), run("failure", at(2), started=None)])
    assert result.episodes_total == 0
    assert result.exclusions == {"invalid_recovery_timestamps": 1}


def test_falha_aberta_iniciada_antes_da_janela_nao_e_novo_episodio():
    result = calculate_recovery([
        run("success", at(1)), run("failure", at(2), started=at(0)),
    ], Window(at(1), at(4)))
    assert result.exclusions == {"failure_started_outside_window": 1}


def test_run_com_created_fora_da_janela_nao_encerra_episodio():
    result = calculate_recovery([
        run("success", at(1)), run("failure", at(2)), run("success", at(5)),
    ], Window(at(0), at(4)))
    assert result.censored_episodes == 1


def test_fronteira_fracionaria_nao_perde_ultimo_segundo():
    window = Window(timestamp("2025-06-01T00:00:00.500Z"), timestamp("2025-06-01T00:00:02.500Z"))
    result, _ = collect(RunsApi([
        raw_run(1, "2025-06-01T00:00:00Z"), raw_run(2, "2025-06-01T00:00:01Z"),
        raw_run(3, "2025-06-01T00:00:02Z"), raw_run(4, "2025-06-01T00:00:03Z"),
    ]), window)
    assert [item.id for item in result] == [2, 3]


def test_campos_invalidos_em_cancelled_nao_abortam_e_sao_contados():
    result, stats = collect(RunsApi([
        raw_run(1, "2025-06-01T00:00:00Z", "cancelled", updated_at="bad"),
        raw_run(2, "2025-06-01T00:00:00Z", "success", updated_at="bad"),
        raw_run(3, "2025-06-01T00:00:00Z"),
    ]))
    assert [item.id for item in result] == [3]
    assert stats["ignored"] == {"cancelled": 1}
    assert stats["exclusions"] == {"invalid_workflow_run": 1}


def test_cache_isola_configuracoes_e_refresh_preserva_as_demais(tmp_path):
    class Counting:
        calls = 0
        def get(self, url):
            self.calls += 1
            return Response({"revision": self.calls}, {})
    source = Counting()
    path = tmp_path / "cache.sqlite3"
    with SQLiteCacheTransport(source, path, namespace="a") as a:
        assert a.get("https://api.github.com/repo").data == {"revision": 1}
    with SQLiteCacheTransport(source, path, namespace="b") as b:
        assert b.get("https://api.github.com/repo").data == {"revision": 2}
    with SQLiteCacheTransport(source, path, namespace="a") as a:
        assert a.get("https://api.github.com/repo").data == {"revision": 1}
        a.clear()
        assert a.get("https://api.github.com/repo").data == {"revision": 3}
        assert a.connection.execute("SELECT fetched_at FROM responses LIMIT 1").fetchone()[0]
    with SQLiteCacheTransport(source, path, namespace="b") as b:
        assert b.get("https://api.github.com/repo").data == {"revision": 2}


def test_consulta_real_individual_inclui_workflows_e_metricas(tmp_path, monkeypatch):
    config = json.loads(STUDY.read_text(encoding="utf-8"))
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    source = PilotTransport(repository_count=1)
    source.runs[1]["conclusion"] = "failure"
    source.runs[2]["updated_at"] = "2025-06-01T01:00:00Z"
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic")
    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: source)
    output = tmp_path / "repo.json"
    args = ["--config", str(path), "--repo", "pilot/project-001",
            "--output", str(output), "--cache", str(tmp_path / "cache.sqlite3")]
    assert main(args) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert len(result["workflow_runs"]) == 50
    assert result["ci_failure_rate"]["rate"] == 1/50
    assert result["recovery"]["median_hours"] == 1
    assert result["configuration"]["values"] == config
    # Retomada não consulta o transporte; refresh deve voltar a consultá-lo.
    def fail(*args, **kwargs):
        raise RuntimeError("transport reached")
    source.get = fail
    assert main(args) == 0
    with pytest.raises(SystemExit) as info:
        main(args + ["--refresh-cache"])
    assert info.value.code == 1


@pytest.mark.parametrize("mutation", ["short_window", "cancelled", "duplicate_factors"])
def test_config_rejeita_criterios_que_distorcem_o_estudo(tmp_path, mutation):
    config = json.loads(STUDY.read_text(encoding="utf-8"))
    if mutation == "short_window":
        config["window"]["end"] = "2025-11-06T00:00:00-03:00"
    elif mutation == "cancelled":
        config["workflow_runs"]["valid_conclusions"].append("cancelled")
    else:
        config["rq06_factors"] = ["stars_quartile"] * 3
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
