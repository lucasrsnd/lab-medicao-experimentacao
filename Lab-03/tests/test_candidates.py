import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from lab03.collectors import candidates
from lab03.collectors.candidates import search_popular_repositories, select_candidates
from lab03.cli import main
from lab03.github import Response, GitHubClient
from lab03.domain import timestamp


class CandidateTransport:
    def __init__(self, *, actions=True, releases=None, runs=None):
        self.actions = actions
        self.releases = releases if releases is not None else [{
            "id": 10,
            "draft": False,
            "prerelease": False,
            "published_at": "2025-06-01T00:00:00Z",
        }]
        self.runs = runs if runs is not None else [
            {"id": 1, "event": "push", "head_branch": "main",
             "created_at": "2025-06-01T00:00:00Z", "conclusion": "success"},
            {"id": 2, "event": "push", "head_branch": "main",
             "created_at": "2025-06-02T00:00:00Z", "conclusion": "failure"},
            {"id": 3, "event": "push", "head_branch": "main",
             "created_at": "2025-06-03T00:00:00Z", "conclusion": "cancelled"},
        ]
        self.calls = []
        self.repository = {
            "id": 5,
            "full_name": "demo/project",
            "stargazers_count": 1500,
            "language": "Python",
            "created_at": "2020-01-01T00:00:00Z",
            "default_branch": "main",
        }

    def get(self, url):
        parsed = urlsplit(url)
        params = parse_qs(parsed.query)
        self.calls.append(parsed.path)
        if parsed.path == "/search/repositories":
            if params.get("per_page") == ["1"]:
                query = params["q"][0]
                if "created:2026-10-05..2026-10-06" in query:
                    return Response({"total_count": 1000}, {})
                return Response({"total_count": 1}, {})
            return Response({"items": [self.repository]}, {})
        if parsed.path.endswith("/actions/workflows"):
            return Response({"total_count": int(self.actions)}, {})
        if parsed.path.endswith("/contributors"):
            return Response([{"id": 1}, {"id": 2}], {})
        if parsed.path.endswith("/releases"):
            return Response([
                {"tag_name": f"v{r['id']}", "body": "release",
                 "html_url": f"https://github.com/demo/project/releases/{r['id']}", **r}
                for r in self.releases
            ], {})
        if parsed.path.endswith("/actions/runs"):
            low, high = (timestamp(v) for v in params["created"][0].split(".."))
            runs = [
                {"workflow_id": 1, "name": "CI", "status": "completed", "head_sha": "h",
                 "run_started_at": r["created_at"], "updated_at": r["created_at"], **r}
                for r in self.runs if low <= timestamp(r["created_at"]) <= high
            ]
            return Response({"total_count": len(runs), "workflow_runs": runs}, {})
        if parsed.path == "/repos/demo/project":
            return Response({"default_branch": "main"}, {})
        if "/commits/" in parsed.path:
            return Response({"sha": parsed.path.rsplit("/", 1)[-1]}, {})
        if "/compare/" in parsed.path:
            return Response({"status": "ahead"}, {})
        raise AssertionError(f"Unexpected request: {url}")


def test_busca_fatia_resultados_e_deduplica_ids(monkeypatch):
    monkeypatch.setattr(candidates, "SEARCH_START", date(2026, 10, 5))
    monkeypatch.setattr(candidates, "_current_search_end", lambda: date(2026, 10, 6))
    transport = CandidateTransport()
    repositories, stats = search_popular_repositories(
        GitHubClient(transport), stars_min_exclusive=1000,
    )
    assert len(repositories) == 1
    assert stats["duplicate_ids"] == 1
    assert stats["query_count"] == 3
    assert len(stats["queries"]) == 3


def test_busca_de_um_dia_fatia_por_faixa_de_estrelas(monkeypatch):
    monkeypatch.setattr(candidates, "SEARCH_START", date(2026, 10, 6))
    monkeypatch.setattr(candidates, "_current_search_end", lambda: date(2026, 10, 6))

    class StarSplitTransport(CandidateTransport):
        def get(self, url):
            parsed = urlsplit(url)
            params = parse_qs(parsed.query)
            if parsed.path == "/search/repositories":
                if params.get("per_page") == ["1"]:
                    query = params["q"][0]
                    count = 1000 if "stars:>" in query else 0
                    self.calls.append(parsed.path)
                    return Response({"total_count": count}, {})
                return Response({"items": []}, {})
            return super().get(url)

    transport = StarSplitTransport()
    repositories, stats = search_popular_repositories(
        GitHubClient(transport), stars_min_exclusive=1000,
    )
    assert repositories == []
    assert stats["query_count"] == 3
    assert any("stars:1001.." in query["query"] for query in stats["queries"])


def test_sem_actions_descartado_antes_das_coletas_custosas():
    transport = CandidateTransport(actions=False)
    output = select_candidates(
        GitHubClient(transport),
        timestamp("2025-01-01T00:00:00Z"),
        timestamp("2026-01-01T00:00:00Z"),
        stars_min_exclusive=1000,
        sample_size=10,
        minimum_releases=1,
        minimum_valid_runs=1,
        valid_conclusions=("success", "failure"),
    )
    assert output["funnel"]["actions"]["excluded"] == {"no_actions": 1}
    assert output["funnel"]["metadata"]["input"] == 0
    assert not any(path.endswith(("/contributors", "/releases", "/actions/runs"))
                   for path in transport.calls)


def test_funil_coleta_metadados_e_aplica_ambos_os_minimos():
    transport = CandidateTransport()
    output = select_candidates(
        GitHubClient(transport),
        timestamp("2025-01-01T00:00:00Z"),
        timestamp("2026-01-01T00:00:00Z"),
        stars_min_exclusive=1000,
        sample_size=10,
        minimum_releases=1,
        minimum_valid_runs=2,
        valid_conclusions=("success", "failure"),
    )
    assert output["funnel"]["releases"]["passed"] == 1
    assert output["funnel"]["workflow_runs"]["passed"] == 1
    assert output["funnel"]["final_eligibility"]["passed"] == 1
    repository = output["eligible_repositories"][0]
    assert repository["contributor_count"] == 2
    assert repository["primary_language"] == "Python"
    assert repository["default_branch"] == "main"
    assert repository["release_count"] == 1
    assert repository["valid_workflow_run_count"] == 2
    assert repository["observed_workflow_run_count"] == 3
    assert repository["age_days_at_collection"] > 0
    assert any(path.endswith("/actions/runs") for path in transport.calls)


def test_filtros_finais_independentes_com_motivos_por_etapa():
    transport = CandidateTransport(releases=[], runs=[])
    output = select_candidates(
        GitHubClient(transport),
        timestamp("2025-01-01T00:00:00Z"),
        timestamp("2026-01-01T00:00:00Z"),
        stars_min_exclusive=1000,
        sample_size=10,
        minimum_releases=1,
        minimum_valid_runs=1,
        valid_conclusions=("success", "failure"),
    )
    assert output["funnel"]["releases"]["excluded"] == {"minimum_releases_not_met": 1}
    assert output["funnel"]["workflow_runs"]["excluded"] == {
        "minimum_valid_workflow_runs_not_met": 1,
    }
    assert output["funnel"]["final_eligibility"]["excluded"] == {
        "minimum_releases_not_met+minimum_valid_workflow_runs_not_met": 1,
    }
    assert any(path.endswith("/actions/runs") for path in transport.calls)
    assert output["eligible_repositories"] == []


def test_cli_gera_artefato_do_funil(tmp_path, monkeypatch):
    config = json.loads(
        (Path(__file__).parents[1] / "config" / "estudo.json").read_text(encoding="utf-8")
    )
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    config["population"]["initial_sprint_sample"] = 1
    config_path = tmp_path / "study.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    output_path = tmp_path / "funnel.json"
    transport = CandidateTransport()
    transport.releases = [
        {"id": index, "draft": False, "prerelease": False,
         "published_at": "2025-06-01T00:00:00Z"}
        for index in range(1, 6)
    ]
    transport.runs = [
        {"id": index, "event": "push", "head_branch": "main",
         "created_at": "2025-06-01T00:00:00Z", "conclusion": "success"}
        for index in range(1, 51)
    ]
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: transport)

    assert main([
        "--config", str(config_path),
        "--select-candidates",
        "--output", str(output_path),
        "--cache", str(tmp_path / "cache.sqlite3"),
    ]) == 0
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["source"] == "github"
    assert output["issue"] == 97
    assert output["funnel"]["final_eligibility"]["passed"] == 1
