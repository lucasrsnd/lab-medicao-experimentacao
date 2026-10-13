from copy import deepcopy
import pytest

from lab03.collectors.releases import collect_releases, repo_path
from lab03.collectors.commits import collect_changes
from lab03.github import ApiError, DataError
from conftest import BASE


def test_releases_paginadas_antecessora_e_variantes(client, window):
    catalog = collect_releases(client, "demo/project", window)
    assert [r.id for r in catalog.history] == [1, 2, 3, 4]
    assert [r.id for r in catalog.releases] == [2, 4]
    assert [r.id for r in catalog.prereleases] == [3]
    assert [tag.name for tag in catalog.tags] == ["v1.1", "v1.2-rc", "v1.2"]
    assert catalog.default_head == "head"
    assert catalog.exclusions == ()


def test_draft_invalidas_duplicadas_e_fronteira(snapshot, client, window):
    original = snapshot[BASE + "/releases?per_page=100"]["data"][1]
    page = snapshot[BASE + "/releases?per_page=100"]["data"]
    for id, field, value in [
        (5, "draft", True), (6, "published_at", None),
        (7, "published_at", "2026-03-01T00:00:00Z"),
    ]:
        item = dict(original, id=id)
        item[field] = value
        page.append(item)
    page.append(deepcopy(original))
    catalog = collect_releases(client, "demo/project", window)
    assert [r.id for r in catalog.releases] == [2, 4]
    assert {e.reason for e in catalog.exclusions} == {"draft", "invalid_published_at"}


def test_nao_confia_no_target_commitish(snapshot, client, window):
    snapshot[BASE + "/compare/b...head?per_page=1"]["data"]["status"] = "diverged"
    catalog = collect_releases(client, "demo/project", window)
    assert [r.id for r in catalog.releases] == [4]
    assert any(e.reason == "outside_default_branch" for e in catalog.exclusions)


def test_tag_apagada_contabilizada(snapshot, client, window):
    snapshot[BASE + "/commits/v1.1"] = {"status": 404, "data": {}}
    catalog = collect_releases(client, "demo/project", window)
    assert [r.id for r in catalog.releases] == [4]
    assert any(e.identifier == "2" and e.reason == "unresolved_ref_404" for e in catalog.exclusions)


def test_coleta_nao_oculta_rate_limit(snapshot, client, window):
    snapshot[BASE + "/commits/v1.1"] = {"status": 403, "data": {}}
    with pytest.raises(ApiError):
        collect_releases(client, "demo/project", window)


def test_nao_pula_antecessora_com_tag_apagada(snapshot, client, window):
    snapshot[BASE + "/commits/v1.1"] = {"status": 404, "data": {}}
    catalog = collect_releases(client, "demo/project", window)
    changes = collect_changes(client, "demo/project", catalog, window)
    assert changes[0].exclusion == "unresolved_release_ref"
    assert changes[1].previous.id == 2
    assert changes[1].exclusion == "unresolved_previous_ref"


def test_antecessora_fora_janela_e_author_date(client, window):
    catalog = collect_releases(client, "demo/project", window)
    changes = collect_changes(client, "demo/project", catalog, window)
    assert changes[0].previous.id == 1
    assert changes[1].previous.id == 2  # pré-release não vira antecessora principal
    assert changes[0].commits[0].authored_at.day == 2
    assert changes[0].commits[0].message == "feat: exemplo"


def test_variante_inclui_pre_release_na_cadeia(client, window):
    catalog = collect_releases(client, "demo/project", window)
    changes = collect_changes(client, "demo/project", catalog, window, include_prereleases=True)
    assert [c.release.id for c in changes] == [2, 3, 4]
    assert [c.previous.id for c in changes] == [1, 2, 3]


def test_compare_mais_de_250_sem_truncamento(snapshot, client, window):
    first_url = BASE + "/compare/a...b?per_page=100"
    template = snapshot[first_url]["data"]["commits"][0]
    commits = [dict(template, sha=f"sha-{n}") for n in range(301)]
    for page_number in range(1, 5):
        url = first_url + (f"&page={page_number}" if page_number > 1 else "")
        snapshot[url] = {
            "data": {"status": "ahead", "total_commits": 301,
                     "commits": commits[(page_number - 1) * 100:page_number * 100]},
            "headers": ({"link": f'<{first_url}&page={page_number+1}>; rel="next"'}
                        if page_number < 4 else {}),
        }
    catalog = collect_releases(client, "demo/project", window)
    assert len(collect_changes(client, "demo/project", catalog, window)[0].commits) == 301


def test_compare_incompleto_falha(snapshot, client, window):
    snapshot[BASE + "/compare/a...b?per_page=100"]["data"]["total_commits"] = 300
    catalog = collect_releases(client, "demo/project", window)
    with pytest.raises(DataError, match="incompleto"):
        collect_changes(client, "demo/project", catalog, window)


@pytest.mark.parametrize(("status", "reason"), [(404, "compare_not_found"), (200, "non_linear_history")])
def test_compare_indisponivel_preserva_exclusao(snapshot, client, window, status, reason):
    snapshot[BASE + "/compare/a...b?per_page=100"] = {
        "status": status, "data": {"status": "diverged"},
    }
    catalog = collect_releases(client, "demo/project", window)
    changes = collect_changes(client, "demo/project", catalog, window)
    assert changes[0].exclusion == reason
    assert not changes[0].commits


def test_primeira_release_sem_antecessora(client, window):
    from dataclasses import replace
    catalog = collect_releases(client, "demo/project", window)
    catalog = replace(catalog, history=(catalog.releases[0],))
    changes = collect_changes(client, "demo/project", catalog, window)
    assert changes[0].exclusion == "no_previous_release"


def test_ref_com_barra_e_codificada(snapshot, client, window):
    snapshot[BASE]["data"]["default_branch"] = "release/main"
    snapshot[BASE + "/commits/release%2Fmain"] = snapshot.pop(BASE + "/commits/main")
    assert collect_releases(client, "demo/project", window).default_branch == "release/main"


@pytest.mark.parametrize("name", ["../x/y", "https://github.com/a/b", "repo", "a/b?token=abc"])
def test_rejeita_repository_invalido(name):
    with pytest.raises(ValueError):
        repo_path(name)


def test_collect_tags_false_nao_consulta_tags(client, window):
    calls = []
    original = client.pages
    client.pages = lambda path, params=None: (calls.append(path), original(path, params))[1]
    catalog = collect_releases(client, "demo/project", window, collect_tags=False)
    assert catalog.tags == ()
    assert not any(path.endswith("/tags") for path in calls)


def test_release_pages_para_na_primeira_pagina_inteira_anterior_a_janela():
    from urllib.parse import parse_qs, urlsplit

    from lab03.collectors.releases import release_pages
    from lab03.domain import timestamp
    from lab03.github import GitHubClient, Response

    def rel(i, date):
        return {"id": i, "draft": False, "prerelease": False, "published_at": date}

    pages = {
        1: [rel(1, "2025-06-01T00:00:00Z"), rel(2, "2025-02-01T00:00:00Z")],
        2: [rel(3, "2024-12-01T00:00:00Z"), rel(4, "2024-11-01T00:00:00Z")],
        3: [rel(5, "2024-10-01T00:00:00Z")],
    }
    requested = []

    class Transport:
        def get(self, url):
            page = int(parse_qs(urlsplit(url).query).get("page", ["1"])[0])
            requested.append(page)
            headers = {}
            if page < 3:
                headers["link"] = ('<https://api.github.com/repos/o/r/releases?per_page=100'
                                   f'&page={page + 1}>; rel="next"')
            return Response(pages[page], headers)

    start = timestamp("2025-01-01T00:00:00Z")
    result = [r["id"] for p in release_pages(GitHubClient(Transport()), "/repos/o/r", start) for r in p]
    assert result == [1, 2, 3, 4] and requested == [1, 2]
