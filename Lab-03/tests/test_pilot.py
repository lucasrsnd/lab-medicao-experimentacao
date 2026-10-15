import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from lab03.domain import Window, timestamp
from lab03.github import GitHubClient, Response
from lab03.cli import main
from lab03.pilot import run_pilot


class PilotTransport:
    def __init__(self, repository_count=100, no_actions=None):
        self.no_actions = set(no_actions or ())
        self.repositories = [
            {
                "id": identifier,
                "full_name": f"pilot/project-{identifier:03d}",
                "stargazers_count": 5000 - identifier,
                "language": "Python",
                "created_at": "2020-01-01T00:00:00Z",
                "default_branch": "main",
            }
            for identifier in range(1, repository_count + 1)
        ]
        self.releases = [
            {
                "id": release_id,
                "draft": False,
                "prerelease": False,
                "published_at": f"2025-{month:02d}-01T00:00:00Z",
                "tag_name": f"v{release_id}",
                "body": "release",
                "html_url": f"https://github.com/pilot/project/releases/{release_id}",
            }
            for release_id, month in enumerate(range(3, 8), start=1)
        ]
        self.runs = [
            {
                "id": run_id,
                "workflow_id": 1,
                "name": "CI",
                "head_branch": "main",
                "event": "push",
                "status": "completed",
                "conclusion": "success",
                "head_sha": f"run-{run_id}",
                "created_at": "2025-06-01T00:00:00Z",
                "run_started_at": "2025-06-01T00:00:00Z",
                "updated_at": "2025-06-01T00:01:00Z",
            }
            for run_id in range(1, 51)
        ]

    def get(self, url):
        parsed = urlsplit(url)
        path = parsed.path
        parts = path.split("/")
        params = parse_qs(parsed.query)
        if path == "/search/repositories":
            if params.get("per_page") == ["1"]:
                return Response({"total_count": len(self.repositories)}, {})
            return Response({"items": self.repositories}, {})
        repository = f"{parts[2]}/{parts[3]}"
        if path.endswith("/actions/workflows"):
            identifier = int(repository.rsplit("-", 1)[1])
            return Response({"total_count": int(identifier not in self.no_actions)}, {})
        if path.endswith("/contributors"):
            return Response([{"id": 1}], {})
        if path.endswith("/actions/runs"):
            low, high = (timestamp(v) for v in params["created"][0].split(".."))
            runs = [r for r in self.runs if low <= timestamp(r["created_at"]) <= high]
            return Response({"total_count": len(runs), "workflow_runs": runs}, {})
        if path.endswith("/releases"):
            return Response(self.releases, {})
        if path.endswith("/tags"):
            return Response([], {})
        if path.endswith("/commits/main"):
            return Response({"sha": "head"}, {})
        if "/commits/v" in path:
            tag = path.rsplit("/", 1)[-1]
            return Response({"sha": tag.replace("/", "-")}, {})
        if "/compare/" in path:
            comparison = path.split("/compare/", 1)[1]
            before, after = comparison.split("...", 1)
            if after == "head":
                return Response({"status": "ahead"}, {})
            commit = {
                "sha": f"{repository}-{after}",
                "commit": {
                    "author": {"date": "2025-05-01T00:00:00Z"},
                    "message": "change",
                },
            }
            return Response({
                "status": "ahead",
                "total_commits": 1,
                "commits": [commit],
            }, {})
        if path == f"/repos/{repository}":
            return Response({"default_branch": "main"}, {})
        raise AssertionError(f"Unexpected request: {url}")


def test_piloto_integrado_coleta_100_elegiveis_com_metadados_releases_commits_runs():
    output = run_pilot(
        GitHubClient(PilotTransport(repository_count=101, no_actions={1})),
        window=Window(
            timestamp("2025-03-01T00:00:00Z"),
            timestamp("2026-03-01T00:00:00Z"),
        ),
        target_size=100,
        stars_min_exclusive=1000,
        minimum_releases=5,
        minimum_valid_runs=50,
        valid_conclusions=("success", "failure", "timed_out", "startup_failure"),
    )

    assert output["issue"] == 106
    assert output["pilot_sample"] == {
        "target": 100,
        "selected": 100,
        "eligible_not_selected": 0,
    }
    assert output["funnel"]["search"]["selected"] == 101
    assert len(output["repositories"]) == 100
    first = output["repositories"][0]
    assert first["metadata"]["contributor_count"] == 1
    assert first["metadata"]["release_count"] == 5
    assert len(first["report"]["catalog"]["releases"]) == 5
    assert len(first["report"]["changes"]) == 5
    assert len(first["workflow_runs"]) == 50


def test_coleta_completa_substitui_candidato_que_perde_releases(monkeypatch):
    import lab03.pilot as pilot_module

    window = Window(
        timestamp("2025-03-01T00:00:00Z"),
        timestamp("2026-03-01T00:00:00Z"),
    )
    candidates = [
        {"full_name": f"pilot/project-{number:03d}", "default_branch": "main"}
        for number in range(1, 5)
    ]
    selection = {
        "collected_at": "2026-03-01T00:00:00+00:00",
        "window": {"start": window.start.isoformat(), "end": window.end.isoformat()},
        "criteria": {},
        "funnel": {},
        "eligible_repositories": candidates,
    }

    monkeypatch.setattr(
        pilot_module,
        "collect_workflow_runs",
        lambda *args, **kwargs: [object()] * 50,
    )

    def collect_report(client, repository, window, workflow_runs, *, collect_tags):
        release_count = 4 if repository.endswith("001") else 5
        return {"catalog": {"releases": [{}] * release_count}}

    monkeypatch.setattr(pilot_module, "run", collect_report)
    collected = []
    output = run_pilot(
        GitHubClient(PilotTransport(repository_count=4)),
        window=window,
        target_size=2,
        stars_min_exclusive=1000,
        minimum_releases=5,
        minimum_valid_runs=50,
        valid_conclusions=("success",),
        top_only=True,
        workers=1,
        include_workflow_runs=False,
        selection=selection,
        on_result=collected.append,
    )

    assert [item["metadata"]["full_name"] for item in collected] == [
        "pilot/project-002",
        "pilot/project-003",
    ]
    assert output["pilot_sample"] == {
        "target": 2,
        "selected": 2,
        "eligible_not_selected": 2,
    }
    assert output["collection_exclusions"] == [{
        "repository": "pilot/project-001",
        "reason": "minimum_releases_not_met_after_collection",
    }]
    assert output["collection_replacements"] == ["pilot/project-003"]


def test_coleta_completa_reserva_mais_candidatos_para_deriva(monkeypatch):
    import lab03.pilot as pilot_module

    window = Window(
        timestamp("2025-03-01T00:00:00Z"),
        timestamp("2026-03-01T00:00:00Z"),
    )
    candidates = [
        {"full_name": f"pilot/project-{number:03d}", "default_branch": "main"}
        for number in range(16)
    ]

    def select_candidates(*args, **kwargs):
        assert kwargs["sample_size"] == 16
        return {
            "collected_at": "2026-03-01T00:00:00+00:00",
            "window": {"start": window.start.isoformat(), "end": window.end.isoformat()},
            "criteria": {},
            "funnel": {"search": {"selected": 16, "matching_candidates": 20}},
            "eligible_repositories": candidates,
        }

    monkeypatch.setattr(pilot_module, "select_candidates", select_candidates)
    monkeypatch.setattr(
        pilot_module,
        "collect_workflow_runs",
        lambda *args, **kwargs: [object()] * 50,
    )
    monkeypatch.setattr(
        pilot_module,
        "run",
        lambda *args, **kwargs: {"catalog": {"releases": [{}] * 5}},
    )
    collected = []

    run_pilot(
        GitHubClient(PilotTransport(repository_count=16)),
        window=window,
        target_size=2,
        stars_min_exclusive=1000,
        minimum_releases=5,
        minimum_valid_runs=50,
        valid_conclusions=("success",),
        top_only=True,
        workers=1,
        include_workflow_runs=False,
        on_result=collected.append,
    )

    assert len(collected) == 2


def test_cli_piloto_registra_execucao_cache_e_contagens(tmp_path, monkeypatch):
    config_path = Path(__file__).parents[1] / "config" / "estudo.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    config_path = tmp_path / "study.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    transport = PilotTransport(repository_count=101, no_actions={1})
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-not-persisted")
    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: transport)
    output_path = tmp_path / "pilot.json"
    cache_path = tmp_path / "cache.sqlite3"

    assert main([
        "--config", str(config_path),
        "--pilot",
        "--output", str(output_path),
        "--cache", str(cache_path),
    ]) == 0

    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["execution"]["counts"] == {
        "eligible_repositories": 100,
        "metadata_records": 100,
        "releases": 500,
        "commits": 400,
        "workflow_runs": 5000,
    }
    assert output["execution"]["cache"]["misses"] > 0
    assert output["execution"]["cache"]["hits"] > 0
    assert b"test-token-not-persisted" not in cache_path.read_bytes()


def test_cli_full_usa_final_sample_minimum_e_registra_o_tipo(tmp_path, monkeypatch):
    config_path = Path(__file__).parents[1] / "config" / "estudo.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    config["population"]["initial_sprint_sample"] = 3
    config["population"]["final_sample_minimum"] = 5
    config_path = tmp_path / "study.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setenv("GITHUB_TOKEN", "test-token-not-persisted")
    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: PilotTransport(repository_count=6))
    output_path = tmp_path / "full.json"

    assert main([
        "--config", str(config_path), "--full",
        "--output", str(output_path), "--cache", str(tmp_path / "c.sqlite3"),
    ]) == 0

    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["sample_kind"] == "full"
    assert len(output["repositories"]) == 5
    assert "--full" in output["execution"]["command"]
    assert "delivery_failure_rate" in output["repositories"][0]["report"]


def test_cli_nao_combina_full_com_pilot(tmp_path):
    config_path = Path(__file__).parents[1] / "config" / "estudo.json"
    try:
        main(["--config", str(config_path), "--full", "--pilot", "--output", str(tmp_path / "x.json")])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("combinação inválida deveria falhar")


def _study_config(tmp_path, final=5):
    config_path = Path(__file__).parents[1] / "config" / "estudo.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["status"] = "ready"
    config["collection_allowed"] = True
    config["window"]["start"] = "2025-03-01T00:00:00Z"
    config["window"]["end"] = "2026-03-01T00:00:00Z"
    config["population"]["initial_sprint_sample"] = 3
    config["population"]["final_sample_minimum"] = final
    path = tmp_path / "study.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_selecao_exportada_permite_dividir_a_coleta_e_juntar_as_partes(tmp_path, monkeypatch):
    from lab03.merge import main as merge_main

    config_path = _study_config(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-not-persisted")
    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: PilotTransport(repository_count=6))
    full = tmp_path / "full.json"
    assert main(["--config", str(config_path), "--full", "--output", str(full),
                 "--cache", str(tmp_path / "a.sqlite3")]) == 0
    whole = json.loads(full.read_text(encoding="utf-8"))
    header = {k: v for k, v in whole.items() if k not in ("repositories", "execution", "sample_kind", "source")}
    selection = tmp_path / "selecao.json"
    selection.write_text(json.dumps(header), encoding="utf-8")

    # Segunda pessoa: sem busca, só a coleta das fatias.
    class NoSearch(PilotTransport):
        def get(self, url):
            assert "/search/repositories" not in url, "a seleção não deve ser refeita"
            return super().get(url)

    monkeypatch.setattr("lab03.cli.HttpTransport", lambda token: NoSearch(repository_count=6))
    parts = []
    for first, last in ((0, 3), (3, 5)):
        out = tmp_path / f"parte_{first}.json"
        assert main(["--config", str(config_path), "--full", "--selection", str(selection),
                     "--slice", f"{first}:{last}", "--output", str(out),
                     "--cache", str(tmp_path / f"c{first}.sqlite3")]) == 0
        parts.append(out)
        assert len(json.loads(out.read_text(encoding="utf-8"))["repositories"]) == last - first

    merged = tmp_path / "merged.json"
    assert merge_main([str(parts[0]), str(parts[1]), "--output", str(merged)]) == 0
    result = json.loads(merged.read_text(encoding="utf-8"))
    assert [r["metadata"]["full_name"] for r in result["repositories"]] == \
           [r["metadata"]["full_name"] for r in whole["repositories"]]
    assert result["execution"]["counts"]["eligible_repositories"] == 5
    # Parte faltando é detectada.
    assert merge_main([str(parts[0]), "--output", str(tmp_path / "x.json"),
                       "--selection", str(selection)]) == 1
