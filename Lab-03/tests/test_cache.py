from pathlib import Path

from lab03.cache import SQLiteCacheTransport
from lab03.github import Response


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
