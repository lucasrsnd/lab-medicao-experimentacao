import pytest
from lab03.github import ApiError, DataError, GitHubClient, Response, SnapshotTransport, HttpTransport
from conftest import BASE


def test_snapshot_nunca_cai_na_rede():
    with pytest.raises(DataError):
        GitHubClient(SnapshotTransport({})).get("/repos/missing/repo")


def test_link_ciclico(snapshot, client):
    snapshot[BASE]["headers"] = {"link": f'<{BASE}>; rel="next"'}
    with pytest.raises(DataError, match="Ciclo"):
        list(client.pages("/repos/demo/project"))


def test_link_externo_nao_recebe_token(snapshot, client):
    snapshot[BASE]["headers"] = {"link": '<https://example.com/steal>; rel="next"'}
    with pytest.raises(ValueError):
        list(client.pages("/repos/demo/project"))


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
def test_erros_http_sanitizados(monkeypatch, status):
    from urllib.error import HTTPError
    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "secret-token", {}, None)
    monkeypatch.setattr("lab03.github.urlopen", fail)
    with pytest.raises(ApiError) as error:
        HttpTransport("secret-token").get(BASE)
    assert error.value.status == status
    assert "secret-token" not in str(error.value)


def test_http_headers_timeout_e_resposta(monkeypatch):
    from io import BytesIO
    class Raw(BytesIO):
        headers = {"Link": '<https://api.github.com/next>; rel="next"'}
    def fetch(request, timeout):
        assert request.get_header("Authorization").startswith("Bearer ")
        assert request.get_header("Authorization").endswith("test-token")
        assert timeout == 12
        return Raw(b'{"ok": true}')
    monkeypatch.setattr("lab03.github.urlopen", fetch)
    result = HttpTransport("test-token", timeout=12).get(BASE)
    assert result.data == {"ok": True}
    assert "link" in result.headers


def test_erro_rede_sem_segredo(monkeypatch):
    from urllib.error import URLError
    def fail(*args, **kwargs):
        raise URLError("secret")
    monkeypatch.setattr("lab03.github.urlopen", fail)
    with pytest.raises(RuntimeError, match="Falha de rede") as error:
        HttpTransport("secret").get(BASE)
    assert "secret" not in str(error.value)


def test_resposta_http_interrompida_e_repetida_sem_cachear_corpo_parcial(monkeypatch, tmp_path):
    from http.client import IncompleteRead
    from io import BytesIO
    from lab03.cache import SQLiteCacheTransport
    from lab03.resilience import ResilientTransport

    class Partial(BytesIO):
        headers = {}
        def read(self, *args):
            raise IncompleteRead(b'{"partial":', 10)

    class Complete(BytesIO):
        headers = {}

    responses = iter([Partial(), Complete(b'{"ok": true}')])
    calls = []
    def fetch(request, **kwargs):
        calls.append(request.full_url)
        return next(responses)
    monkeypatch.setattr('lab03.github.urlopen', fetch)
    delays = []
    resilient = ResilientTransport(HttpTransport('test-token'), sleep=delays.append)
    with SQLiteCacheTransport(resilient, tmp_path / 'cache.sqlite3') as cache:
        assert cache.get(BASE).data == {'ok': True}
        assert cache.get(BASE).data == {'ok': True}
        assert cache.hits == 1
    assert len(calls) == 2
    assert delays == [1.0]

