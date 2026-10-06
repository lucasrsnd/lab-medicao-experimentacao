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
        assert request.get_header("Authorization") == "Bearer test-token"
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

