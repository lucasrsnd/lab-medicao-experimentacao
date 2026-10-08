"""A busca parcial preserva a ordem por estrelas/ID e não perde empates."""

from urllib.parse import parse_qs, urlsplit

import pytest

from lab03.collectors.candidates import search_popular_repositories
from lab03.github import DataError, GitHubClient, Response
from lab03.domain import Window, timestamp
from lab03.pilot import run_pilot
from test_pilot import PilotTransport


class RankedSearch:
    def __init__(self, incomplete=False, short=False):
        self.calls = []
        self.incomplete = incomplete
        self.short = short

    def get(self, url):
        self.calls.append(url)
        query = parse_qs(urlsplit(url).query)
        tied = "stars:2000..2000" in query["q"][0]
        if query["per_page"] == ["1"]:
            return Response({"total_count": 3 if tied else 5000}, {})
        if tied:
            return Response({"items": [
                {"id": i, "stargazers_count": 2000} for i in (8, 2, 9)
            ]}, {})
        assert query["sort"] == ["stars"]
        assert query["order"] == ["desc"]
        items = [{"id": 5, "stargazers_count": 3000}]
        if not self.short:
            items.append({"id": 8, "stargazers_count": 2000})
        return Response({"items": items, "incomplete_results": self.incomplete}, {})


def test_prefixo_completa_empate_sem_buscar_toda_populacao():
    transport = RankedSearch()
    records, stats = search_popular_repositories(GitHubClient(transport), 1000, limit=2)
    selected = sorted(records, key=lambda r: (-r["stargazers_count"], r["id"]))[:2]
    assert [r["id"] for r in selected] == [5, 2]
    assert stats["population_count"] == 5000
    assert stats["unique_candidates"] == 4
    assert stats["duplicate_ids"] == 1
    assert len(transport.calls) == 4
    assert stats["queries"][0]["purpose"] == "ranked_prefix"


@pytest.mark.parametrize("options", [{"incomplete": True}, {"short": True}])
def test_prefixo_rejeita_busca_incompleta(options):
    with pytest.raises(DataError):
        search_popular_repositories(GitHubClient(RankedSearch(**options)), 1000, limit=2)


@pytest.mark.parametrize("required_id, expected", [(1, [1, 2]), (3, [3, 1])])
def test_piloto_inclui_repositorio_explicito_sem_duplicar(required_id, expected):
    class WithMetadata(PilotTransport):
        def get(self, url):
            path = urlsplit(url).path
            for record in self.repositories:
                if path == '/repos/' + record['full_name']:
                    return Response({**record, 'private': False}, {})
            return super().get(url)

    output = run_pilot(
        GitHubClient(WithMetadata(repository_count=3)),
        window=Window(timestamp('2025-03-01T00:00:00Z'), timestamp('2026-03-01T00:00:00Z')),
        target_size=2, stars_min_exclusive=1000, minimum_releases=5,
        minimum_valid_runs=50, valid_conclusions=('success', 'failure'),
        required_repositories=(f'pilot/project-{required_id:03d}',),
    )
    assert [r['metadata']['id'] for r in output['repositories']] == expected
    assert output['funnel']['search']['selection_policy'] == 'required_then_stars_desc_id_asc'


def test_piloto_nao_forca_inclusao_de_repositorio_inelegivel():
    class WithoutActions(PilotTransport):
        def get(self, url):
            if urlsplit(url).path == '/repos/pilot/project-001':
                return Response({**self.repositories[0], 'private': False}, {})
            return super().get(url)

    with pytest.raises(DataError, match='obrigatórios não elegíveis'):
        run_pilot(
            GitHubClient(WithoutActions(repository_count=1, no_actions={1})),
            window=Window(timestamp('2025-03-01T00:00:00Z'), timestamp('2026-03-01T00:00:00Z')),
            target_size=1, stars_min_exclusive=1000, minimum_releases=5,
            minimum_valid_runs=50, valid_conclusions=('success', 'failure'),
            required_repositories=('pilot/project-001',),
        )
