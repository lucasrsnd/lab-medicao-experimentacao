from pathlib import Path

import pytest

from lab03.cache import SQLiteCacheTransport
from lab03.github import ApiError, Response


class CountingTransport:
    def __init__(self):
        self.calls = 0

    def get(self, url):
        self.calls += 1
        return Response({"url": url}, {
            "link": '<https://api.github.com/next>; rel="next"',
            "authorization": "must-not-be-cached",
        })


def test_cache_sqlite_persiste_respostas_e_headers_de_paginacao(tmp_path: Path):
    database = tmp_path / "cache.sqlite3"
    transport = CountingTransport()
    first_run = SQLiteCacheTransport(transport, database)
    response = first_run.get("https://api.github.com/repos/demo/project")
    assert response.headers["link"].endswith('rel="next"')
    assert "authorization" not in response.headers
    assert first_run.misses == 1

    resumed_run = SQLiteCacheTransport(transport, database)
    resumed = resumed_run.get("https://api.github.com/repos/demo/project")
    assert resumed.data == response.data
    assert resumed.headers == response.headers
    assert resumed_run.hits == 1
    assert transport.calls == 1


class FailingTransport:
    def __init__(self, status):
        self.status = status
        self.calls = 0

    def get(self, url):
        self.calls += 1
        raise ApiError(self.status, url, {"retry-after": "9"})


def test_404_e_persistido_e_nao_repete_chamada_na_retomada(tmp_path: Path):
    database = tmp_path / "cache.sqlite3"
    transport = FailingTransport(404)
    url = "https://api.github.com/repos/demo/project/compare/a...b"
    for _ in range(2):
        with SQLiteCacheTransport(transport, database) as cache:
            with pytest.raises(ApiError) as error:
                cache.get(url)
            assert error.value.status == 404
    assert transport.calls == 1


@pytest.mark.parametrize("status", [401, 403, 429, 500, 502])
def test_erros_transitorios_e_de_autenticacao_nao_sao_cacheados(tmp_path: Path, status):
    transport = FailingTransport(status)
    with SQLiteCacheTransport(transport, tmp_path / "c.sqlite3") as cache:
        for _ in range(2):
            with pytest.raises(ApiError):
                cache.get("https://api.github.com/x")
        assert len(cache) == 0
    assert transport.calls == 2


def test_retomada_apos_interrupcao_so_busca_o_que_falta(tmp_path: Path):
    database = tmp_path / "cache.sqlite3"
    urls = [f"https://api.github.com/repos/demo/p{i}" for i in range(5)]

    class InterruptedAt3(CountingTransport):
        def get(self, url):
            if self.calls == 3:
                raise KeyboardInterrupt
            return super().get(url)

    first = InterruptedAt3()
    cache = SQLiteCacheTransport(first, database)
    with pytest.raises(KeyboardInterrupt):
        for url in urls:
            cache.get(url)
    cache.close()

    second = CountingTransport()
    with SQLiteCacheTransport(second, database) as resumed:
        for url in urls:
            resumed.get(url)
        assert resumed.hits == 3 and resumed.misses == 2
    assert second.calls == 2


def test_cache_antigo_sem_coluna_status_e_migrado(tmp_path: Path):
    database = tmp_path / "old.sqlite3"
    import sqlite3
    old = sqlite3.connect(database)
    old.execute("CREATE TABLE responses (url TEXT PRIMARY KEY, data TEXT NOT NULL, headers TEXT NOT NULL)")
    old.execute("INSERT INTO responses VALUES ('https://api.github.com/a', '{\"v\": 1}', '{}')")
    old.commit()
    old.close()
    with SQLiteCacheTransport(CountingTransport(), database) as cache:
        assert cache.get("https://api.github.com/a").data == {"v": 1}
        assert cache.hits == 1


def test_linha_corrompida_e_refeita(tmp_path: Path):
    database = tmp_path / "cache.sqlite3"
    transport = CountingTransport()
    with SQLiteCacheTransport(transport, database) as cache:
        cache.get("https://api.github.com/a")
        cache.connection.execute("UPDATE responses SET data = '{truncado'")
        cache.connection.commit()
        assert cache.get("https://api.github.com/a").data == {"url": "https://api.github.com/a"}
    assert transport.calls == 2
