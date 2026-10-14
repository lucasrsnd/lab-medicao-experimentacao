import csv
import json
from urllib.parse import urlencode

import pytest

from lab03.cache import compact
from lab03.collectors.commits import collect_changes
from lab03.collectors.tags import collect_tag_history, tag_catalog
from lab03.complement import complement_repository
from lab03.github import GitHubClient, SnapshotTransport
from lab03.variants import NOT_COLLECTED, compute_variants, export
from conftest import BASE

SINCE = BASE + "/commits?" + urlencode({"sha": "head", "since": "2025-03-01T00:00:00Z", "per_page": 100})
UNTIL = BASE + "/commits?" + urlencode({"sha": "head", "until": "2025-03-01T00:00:00Z", "per_page": 100})


def commit(sha, date, message="feat: x"):
    return {"sha": sha, "commit": {"message": message, "author": {"date": date}}}


def page(data, next_url=None):
    return {"data": data, "headers": {"link": f'<{next_url}>; rel="next"'} if next_url else {}}


def compare(commits):
    return page({"status": "ahead", "total_commits": len(commits), "commits": commits})


@pytest.fixture
def tag_responses():
    return {
        BASE + "/tags?per_page=100": page([
            {"name": "v1.2", "commit": {"sha": "c2"}},
            {"name": "v1.1", "commit": {"sha": "c1"}},
            {"name": "latest", "commit": {"sha": "c1"}},
            {"name": "v1.0", "commit": {"sha": "c0"}},
            {"name": "feature-x", "commit": {"sha": "cx"}},
        ]),
        SINCE: page([
            commit("c2", "2025-06-01T00:00:00Z"), commit("m1", "2025-05-01T00:00:00Z"),
            commit("c1", "2025-04-01T00:00:00Z"),
        ]),
        UNTIL: page([commit("m0", "2025-02-01T00:00:00Z")], UNTIL + "&page=2"),
        UNTIL + "&page=2": page([commit("c0", "2025-01-10T00:00:00Z")]),
        BASE + "/compare/c0...c1?per_page=100": compare([
            commit("m0", "2025-02-01T00:00:00Z"), commit("c1", "2025-04-01T00:00:00Z"),
        ]),
        BASE + "/compare/c1...c2?per_page=100": compare([
            commit("m1", "2025-05-01T00:00:00Z"), commit("c2", "2025-06-01T00:00:00Z"),
        ]),
    }


def test_tags_agrupam_commit_e_buscam_antecessora(tag_responses, window):
    client = GitHubClient(SnapshotTransport(tag_responses))
    history = collect_tag_history(client, "demo/project", window, "head")
    assert [(t.sha, t.names) for t in history.deliveries] == [
        ("c0", ("v1.0",)), ("c1", ("latest", "v1.1")), ("c2", ("v1.2",)),
    ]
    assert history.predecessor_status == "found"
    assert (history.tags_total, history.tags_in_window, history.tagged_commits_in_window) == (5, 3, 2)
    assert history.tags_unmatched == 1  # feature-x: fora do branch ou da janela

    catalog = tag_catalog("demo/project", history, window, "main", "head")
    assert [r.sha for r in catalog.releases] == ["c1", "c2"]
    changes = collect_changes(client, "demo/project", catalog, window)
    assert [(c.previous.sha, len(c.commits)) for c in changes] == [("c0", 2), ("c1", 2)]


def test_limite_da_busca_nao_presume_antecessora(tag_responses, window):
    client = GitHubClient(SnapshotTransport(tag_responses))
    history = collect_tag_history(client, "demo/project", window, "head", predecessor_max_pages=1)
    assert history.predecessor_status == "search_limit_reached"
    assert [t.sha for t in history.deliveries] == ["c1", "c2"]
    catalog = tag_catalog("demo/project", history, window, "main", "head")
    changes = collect_changes(client, "demo/project", catalog, window)
    assert changes[0].exclusion == "no_previous_release"


def test_sem_tags_nao_lista_commits(window):
    client = GitHubClient(SnapshotTransport({BASE + "/tags?per_page=100": page([])}))
    history = collect_tag_history(client, "demo/project", window, "head")
    assert history.deliveries == () and history.predecessor_status == "not_needed"


def test_cache_compacta_tags_e_listagem_de_commits():
    tags = compact(BASE + "/tags?per_page=100", [
        {"name": "v1", "zipball_url": "x", "commit": {"sha": "a", "url": "y"}},
    ])
    assert tags == [{"name": "v1", "commit": {"sha": "a"}}]
    commits = compact(SINCE, [{
        "sha": "a", "parents": [], "author": {"login": "x"},
        "commit": {"message": "m", "author": {"date": "d", "name": "n"}, "committer": {"date": "e"}},
    }])
    assert commits == [{"sha": "a", "commit": {"author": {"date": "d"}, "committer": {"date": "e"}}}]


def release(id, tag, sha, published, prerelease=False):
    return {"id": id, "tag": tag, "sha": sha, "published_at": published,
            "prerelease": prerelease, "notes": "", "url": f"https://x/{tag}"}


def dataset_item():
    old = release(1, "v1.0.0", "c0", "2025-01-01T00:00:00+00:00")
    stable = [release(2, "v1.1.0", "c1", "2025-04-02T00:00:00+00:00"),
              release(4, "v1.1.1", "c2", "2025-06-02T00:00:00+00:00")]
    pre = release(3, "v1.1.1-rc1", "m1", "2025-05-02T00:00:00+00:00", prerelease=True)
    return {
        "metadata": {"full_name": "demo/project"},
        "report": {
            "catalog": {"default_branch": "main", "default_head": "head",
                        "history": [old, stable[0], pre, stable[1]],
                        "releases": stable, "prereleases": [pre]},
            "deployment_frequency": {"releases_in_window": 2, "window_weeks": 52.0,
                                     "releases_per_week": 2 / 52},
            "lead_time": {"by_release_hours": 900.0, "releases_used": 2},
            "ci_failure_rate": {"rate": 0.0, "failures": 0, "runs_evaluated": 60},
            "recovery": {"median_hours": None, "episodes_recovered": 0,
                         "episodes_total": 0, "exclusions": {}},
        },
    }


def test_complemento_compara_cadeia_c2_e_tags(tag_responses, window):
    tag_responses[BASE + "/compare/c1...m1?per_page=100"] = compare([
        commit("m1", "2025-05-01T00:00:00Z", "fix: crash"),
    ])
    tag_responses[BASE + "/compare/m1...c2?per_page=100"] = compare([
        commit("c2", "2025-06-01T00:00:00Z", "fix: regressão"),
    ])
    client = GitHubClient(SnapshotTransport(tag_responses))
    entry = complement_repository(client, dataset_item(), window)
    c2 = entry["c2"]
    assert [c["previous_tag"] for c in c2["changes"]] == ["v1.0.0", "v1.1.0", "v1.1.1-rc1"]
    assert c2["deliveries_in_window"] == 3
    # v1.1.0 (02/04) não tem corretiva em 7 dias; rc1 (02/05) idem; nenhuma censurada.
    assert c2["delivery_failure_rate"]["evaluated"] == 3
    assert entry["c3"]["deployment_frequency"]["releases_in_window"] == 2
    assert entry["c3"]["lead_time"]["commits_used"] == 4


def test_variantes_sem_complemento_ficam_ausentes_e_nao_zero():
    variants = compute_variants(dataset_item(), None, cfr_b_validation="pending")
    c1 = variants["C1"]["classification"]
    assert c1["metrics"]["change_failure_rate"]["value"] == 0.0  # zero observado é dado
    assert c1["overall"]["missing_metrics"] == ["recovery_time_hours"]
    c3 = variants["C3"]["classification"]["metrics"]
    assert c3["deployment_frequency_per_week"]["value"] is None
    assert c3["deployment_frequency_per_week"]["missing_reason"] == NOT_COLLECTED
    c2 = variants["C2"]
    assert c2["classification"]["metrics"]["deployment_frequency_per_week"]["numerator"] == 3
    assert c2["classification"]["metrics"]["change_failure_rate"]["missing_reason"] == NOT_COLLECTED
    assert c2["pending_validations"] == ["corrective_release_heuristic_gold_sample"]


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_exportacao_marca_cobertura_parcial_e_celulas_vazias(tmp_path, tag_responses, window):
    tag_responses[BASE + "/compare/c1...m1?per_page=100"] = compare([commit("m1", "2025-05-01T00:00:00Z")])
    tag_responses[BASE + "/compare/m1...c2?per_page=100"] = compare([commit("c2", "2025-06-01T00:00:00Z")])
    window_json = {"start": "2025-03-01T00:00:00+00:00", "end": "2026-03-01T00:00:00+00:00"}
    other = dict(dataset_item(), metadata={"full_name": "demo/other"})
    dataset = write(tmp_path / "parte.json", {"window": window_json,
                                              "repositories": [dataset_item(), other]})
    from lab03.complement import file_sha256
    entry = complement_repository(GitHubClient(SnapshotTransport(tag_responses)), dataset_item(), window)
    complement = write(tmp_path / "comp.json", json.loads(json.dumps({
        "kind": "rq07_variant_complement", "window": window_json,
        "dataset": {"sha256": file_sha256(dataset)}, "repositories": [entry],
    }, default=str)))
    selection = write(tmp_path / "sel.json", {"window": window_json, "eligible_repositories": [
        {"full_name": "demo/project"}, {"full_name": "demo/other"}, {"full_name": "demo/faltante"},
    ]})
    metadata = export([dataset], [complement], tmp_path / "out", selection)
    assert metadata["coverage"]["status"] == "partial"
    assert metadata["coverage"]["repositories_missing_dataset"] == ["demo/faltante"]
    assert metadata["coverage"]["repositories_without_complement"] == ["demo/other"]
    assert metadata["cfr_b_heuristic_validation"]["status"] == "pending"
    with (tmp_path / "out" / "variantes_metricas.csv").open(encoding="utf-8") as handle:
        rows = {(r["repositorio"], r["variante"]): r for r in csv.DictReader(handle)}
    assert len(rows) == 6
    missing = rows[("demo/other", "C3")]
    assert missing["deployment_frequency_per_week_valor"] == ""
    assert missing["deployment_frequency_per_week_motivo_ausencia"] == NOT_COLLECTED
    assert rows[("demo/project", "C3")]["deployment_frequency_per_week_numerador"] == "2"
    assert rows[("demo/project", "C1")]["recovery_episodes_censored"] == "0"
    assert int(rows[("demo/project", "C2")]["cfr_b_releases_censored"]) >= 0


def test_exportacao_rejeita_complemento_de_outro_dataset(tmp_path):
    window_json = {"start": "2025-03-01T00:00:00+00:00", "end": "2026-03-01T00:00:00+00:00"}
    dataset = write(tmp_path / "parte.json", {"window": window_json, "repositories": [dataset_item()]})
    complement = write(tmp_path / "comp.json", {
        "kind": "rq07_variant_complement", "window": window_json,
        "dataset": {"sha256": "outro"}, "repositories": [],
    })
    with pytest.raises(ValueError, match="dataset não informado"):
        export([dataset], [complement], tmp_path / "out")


def test_avaliacao_da_heuristica_exige_mesma_versao(tmp_path):
    from lab03.variants import heuristic_validation
    evaluation = write(tmp_path / "f1.json", {"heuristic_version": "v2", "f1": 0.8})
    assert heuristic_validation(evaluation, {"v2"})["status"] == "validated"
    with pytest.raises(ValueError):
        heuristic_validation(evaluation, {"v1"})
    low = write(tmp_path / "low.json", {"heuristic_version": "v2", "f1": 0.5})
    assert heuristic_validation(low, {"v2"})["status"] == "below_threshold"
