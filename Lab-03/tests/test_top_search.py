"""Busca dos mais estrelados sem enumerar a população inteira (S02)."""
import re
from urllib.parse import parse_qs, urlsplit

import pytest

from lab03.collectors.candidates import _count_valid_runs, search_top_repositories
from lab03.domain import timestamp
from lab03.github import DataError, GitHubClient, Response


class StarsTransport:
    """População sintética: ids 1..n, estrelas decrescentes; teto de 1.000 por consulta."""

    def __init__(self, stars):
        self.repos = [{"id": i + 1, "full_name": f"o/r{i + 1}", "stargazers_count": s}
                      for i, s in enumerate(stars)]
        self.calls = 0

    def get(self, url):
        self.calls += 1
        parsed = urlsplit(url)
        params = parse_qs(parsed.query)
        match = re.search(r"stars:(\d+)\.\.(\d+)", params["q"][0])
        if match:
            low, high = int(match[1]), int(match[2])
        else:
            low, high = int(re.search(r"stars:>(\d+)", params["q"][0])[1]) + 1, 10**9
        inside = [r for r in self.repos if low <= r["stargazers_count"] <= high]
        inside.sort(key=lambda r: -r["stargazers_count"])
        if params.get("per_page") == ["1"]:
            return Response({"total_count": len(inside)}, {})
        page = int(params.get("page", ["1"])[0])
        chunk = inside[:1000][(page - 1) * 100: page * 100]
        headers = {}
        if page * 100 < min(len(inside), 1000):
            headers["link"] = (f'<https://api.github.com/search/repositories?q={params["q"][0]}'
                               f'&sort=stars&order=desc&per_page=100&page={page + 1}>; rel="next"')
        return Response({"items": chunk, "incomplete_results": False,
                         "total_count": len(inside)}, headers)


def test_populacao_pequena_usa_uma_faixa_e_poucas_paginas():
    transport = StarsTransport(range(5000, 4700, -1))  # 300 repos
    records, info = search_top_repositories(GitHubClient(transport), 1000, 150)
    assert len(records) == 150
    assert [r["stargazers_count"] for r in records] == list(range(5000, 4850, -1))
    assert info["population_total"] == 300 and info["query_count"] == 1
    assert transport.calls <= 5  # contagem total + contagem da faixa + 2 páginas


def test_desce_por_faixas_quando_passa_de_1000_e_deduplica_empates():
    stars = [10_000 - i // 2 for i in range(2500)]  # pares de repos com a mesma estrela
    transport = StarsTransport(stars)
    records, info = search_top_repositories(GitHubClient(transport), 1000, 1500)
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)) == 1500
    assert info["query_count"] == 2
    assert min(r["stargazers_count"] for r in records) <= 10_000 - 1000 // 2


def test_limite_maior_que_a_populacao_devolve_tudo():
    records, _ = search_top_repositories(GitHubClient(StarsTransport([3000, 2000, 1500])), 1000, 10)
    assert len(records) == 3


def test_empate_acima_do_teto_falha_em_vez_de_omitir():
    with pytest.raises(DataError):
        search_top_repositories(GitHubClient(StarsTransport([2000] * 1200)), 1000, 1100)


class RunsTransport:
    def __init__(self, count):
        self.requests = 0
        self.runs = [{"id": i, "event": "push", "head_branch": "main",
                      "created_at": "2025-06-01T00:00:00Z", "conclusion": "success"}
                     for i in range(count)]

    def get(self, url):
        self.requests += 1
        page = int(parse_qs(urlsplit(url).query).get("page", ["1"])[0])
        chunk = self.runs[(page - 1) * 100: page * 100]
        headers = {}
        if page * 100 < len(self.runs):
            headers["link"] = ('<https://api.github.com/repos/o/r/actions/runs?branch=main&event=push'
                               f'&per_page=100&page={page + 1}>; rel="next"')
        return Response({"total_count": len(self.runs), "workflow_runs": chunk}, headers)


WINDOW = (timestamp("2025-01-01T00:00:00Z"), timestamp("2026-01-01T00:00:00Z"))


def test_contagem_de_runs_para_assim_que_o_minimo_e_atingido():
    transport = RunsTransport(5000)
    count, _ = _count_valid_runs(GitHubClient(transport), "/repos/o/r", "main", *WINDOW,
                                 ("success", "failure"), stop_at=50)
    assert count >= 50 and transport.requests == 1


def test_contagem_de_runs_sem_stop_at_continua_exaustiva():
    transport = RunsTransport(250)
    count, observed = _count_valid_runs(GitHubClient(transport), "/repos/o/r", "main", *WINDOW,
                                        ("success", "failure"))
    assert (count, observed) == (250, 250) and transport.requests == 3


def test_contribuidores_403_no_modo_rapido_vira_ausencia_nao_erro():
    from lab03.collectors.candidates import _contributor_count
    from lab03.github import ApiError

    class Forbidden:
        def get(self, url):
            raise ApiError(403, url)

    assert _contributor_count(GitHubClient(Forbidden()), "/repos/torvalds/linux", True) is None


def test_contribuidores_outros_erros_continuam_interrompendo():
    from lab03.collectors.candidates import _contributor_count
    from lab03.github import ApiError

    class Boom:
        def get(self, url):
            raise ApiError(500, url)

    with pytest.raises(ApiError):
        _contributor_count(GitHubClient(Boom()), "/repos/o/r")


def test_contagem_rapida_de_contribuidores_le_a_ultima_pagina_do_link():
    from lab03.collectors.candidates import _contributor_count

    class Paged:
        def __init__(self, headers, data):
            self.headers, self.data, self.urls = headers, data, []

        def get(self, url):
            self.urls.append(url)
            return Response(self.data, self.headers)

    link = ('<https://api.github.com/repositories/1/contributors?anon=1&per_page=1&page=2>; rel="next", '
            '<https://api.github.com/repositories/1/contributors?anon=1&per_page=1&page=4321>; rel="last"')
    transport = Paged({"link": link}, [{"id": 1}])
    assert _contributor_count(GitHubClient(transport), "/repos/o/r", fast=True) == 4321
    assert transport.urls == ["https://api.github.com/repos/o/r/contributors?anon=1&per_page=1"]
    assert _contributor_count(GitHubClient(Paged({}, [{"id": 1}])), "/repos/o/r", fast=True) == 1
    assert _contributor_count(GitHubClient(Paged({}, [])), "/repos/o/r", fast=True) == 0


def test_parallel_map_preserva_ordem_e_propaga_excecao():
    from lab03.collectors.candidates import parallel_map

    assert parallel_map(lambda x: x * 2, range(20), workers=4) == [x * 2 for x in range(20)]
    assert parallel_map(lambda x: x, [], workers=4) == []

    def boom(x):
        if x == 3:
            raise RuntimeError("falhou")
        return x

    with pytest.raises(RuntimeError):
        parallel_map(boom, range(6), workers=3)


def test_cache_sqlite_aguenta_threads(tmp_path):
    from lab03.cache import SQLiteCacheTransport
    from lab03.collectors.candidates import parallel_map

    class Fake:
        def get(self, url):
            return Response({"url": url}, {})

    with SQLiteCacheTransport(Fake(), tmp_path / "c.sqlite3") as cache:
        urls = [f"https://api.github.com/x/{i % 10}" for i in range(200)]
        out = parallel_map(lambda u: cache.get(u).data["url"], urls, workers=8)
        assert out == urls
        assert len(cache) == 10


def test_candidato_com_5xx_persistente_e_excluido_com_motivo_no_modo_rapido():
    from datetime import datetime, timezone

    from lab03.collectors.candidates import select_candidates
    from lab03.github import ApiError

    class Flaky:
        def get(self, url):
            if "/search/repositories" in url:
                if "per_page=1&" in url or url.endswith("per_page=1"):
                    return Response({"total_count": 1}, {})
                return Response({"items": [{
                    "id": 5, "full_name": "o/big", "stargazers_count": 5000, "language": "C",
                    "created_at": "2020-01-01T00:00:00Z", "default_branch": "main"}]}, {})
            if url.endswith("/actions/workflows?per_page=1"):
                return Response({"total_count": 1}, {})
            if "/contributors" in url:
                return Response([{"id": 1}], {})
            if "/releases" in url:
                raise ApiError(504, url)
            raise AssertionError(url)

    output = select_candidates(
        GitHubClient(Flaky()), timestamp("2025-01-01T00:00:00Z"), timestamp("2026-01-01T00:00:00Z"),
        stars_min_exclusive=1000, sample_size=5, minimum_releases=1, minimum_valid_runs=1,
        valid_conclusions=("success",), top_only=True,
    )
    assert output["eligible_repositories"] == []
    assert output["funnel"]["measure_errors"] == {"api_error_504": 1}


def test_candidato_removido_e_excluido_com_404_no_modo_rapido():
    from datetime import datetime, timezone

    from lab03.collectors.candidates import select_candidates
    from lab03.github import ApiError

    class RemovedRepository:
        def get(self, url):
            if "/search/repositories" in url:
                if "per_page=1&" in url or url.endswith("per_page=1"):
                    return Response({"total_count": 1}, {})
                return Response({"items": [{
                    "id": 5, "full_name": "o/removed", "stargazers_count": 5000, "language": "C",
                    "created_at": "2020-01-01T00:00:00Z", "default_branch": "main"}]}, {})
            if url.endswith("/actions/workflows?per_page=1"):
                return Response({"total_count": 1}, {})
            if "/contributors" in url:
                return Response([{"id": 1}], {})
            if "/releases" in url:
                raise ApiError(404, url)
            raise AssertionError(url)

    output = select_candidates(
        GitHubClient(RemovedRepository()),
        timestamp("2025-01-01T00:00:00Z"),
        timestamp("2026-01-01T00:00:00Z"),
        stars_min_exclusive=1000,
        sample_size=5,
        minimum_releases=1,
        minimum_valid_runs=1,
        valid_conclusions=("success",),
        top_only=True,
    )
    assert output["eligible_repositories"] == []
    assert output["funnel"]["measure_errors"] == {"api_error_404": 1}


def test_parallel_stream_entrega_na_ordem_sem_acumular():
    from lab03.collectors.candidates import parallel_stream

    seen = []
    parallel_stream(lambda x: x * 10, range(30), seen.append, workers=4)
    assert seen == [x * 10 for x in range(30)]
    seen.clear()
    parallel_stream(lambda x: x, range(3), seen.append, workers=1)
    assert seen == [0, 1, 2]
