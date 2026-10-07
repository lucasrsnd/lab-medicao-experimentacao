import pytest

from lab03.github import ApiError, NetworkError, Response
from lab03.resilience import RateLimitExhausted, ResilientTransport

URL = "https://api.github.com/repos/demo/project"
SEARCH = "https://api.github.com/search/repositories?q=stars:%3E1000"


class Script:
    """Transporte que devolve/levanta itens em ordem e registra as chamadas."""

    def __init__(self, *items):
        self.items = list(items)
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(**headers):
    return Response({"ok": True}, headers)


def make(transport, now=1_000.0, **kwargs):
    sleeps = []
    resilient = ResilientTransport(
        transport, sleep=sleeps.append, clock=lambda: now, **kwargs,
    )
    return resilient, sleeps


def test_5xx_usa_backoff_exponencial_1_2_4():
    script = Script(ApiError(502, URL), ApiError(503, URL), ApiError(500, URL), ok())
    resilient, sleeps = make(script)
    assert resilient.get(URL).data == {"ok": True}
    assert sleeps == [1, 2, 4]
    assert resilient.retries == 3


def test_backoff_respeita_teto_e_limite_de_tentativas():
    script = Script(*[ApiError(500, URL) for _ in range(4)])
    resilient, sleeps = make(script, max_retries=3, max_delay=2)
    with pytest.raises(ApiError) as error:
        resilient.get(URL)
    assert error.value.status == 500
    assert sleeps == [1, 2, 2]
    assert len(script.calls) == 4


def test_falha_de_rede_e_repetida():
    script = Script(NetworkError("x"), ok())
    resilient, sleeps = make(script)
    assert resilient.get(URL).data == {"ok": True}
    assert sleeps == [1]


def test_falha_de_rede_persistente_propaga():
    script = Script(NetworkError("x"), NetworkError("x"))
    resilient, _ = make(script, max_retries=1)
    with pytest.raises(NetworkError):
        resilient.get(URL)


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_erros_do_cliente_nao_sao_repetidos(status):
    script = Script(ApiError(status, URL))
    resilient, sleeps = make(script)
    with pytest.raises(ApiError):
        resilient.get(URL)
    assert sleeps == [] and len(script.calls) == 1


def test_403_de_permissao_sem_sinal_de_limite_nao_e_repetido():
    script = Script(ApiError(403, URL, {"x-ratelimit-remaining": "42"}))
    resilient, sleeps = make(script)
    with pytest.raises(ApiError):
        resilient.get(URL)
    assert sleeps == []


def test_403_com_cota_zerada_espera_ate_o_reset_e_repete():
    limit = ApiError(403, URL, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1090"})
    script = Script(limit, ok())
    resilient, sleeps = make(script, now=1_000.0)
    assert resilient.get(URL).data == {"ok": True}
    assert sleeps == [91.0]  # 1090 - 1000 + 1s de margem
    assert resilient.rate_limit_waits == 1


def test_limite_secundario_usa_retry_after():
    limit = ApiError(403, URL, {"retry-after": "30"})
    script = Script(limit, ok())
    resilient, sleeps = make(script)
    resilient.get(URL)
    assert sleeps == [31.0]


def test_429_sem_cabecalhos_usa_espera_padrao():
    script = Script(ApiError(429, URL), ok())
    resilient, sleeps = make(script)
    resilient.get(URL)
    assert sleeps == [60.0]


def test_reset_no_passado_nao_gera_espera_negativa():
    limit = ApiError(403, URL, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "10"})
    script = Script(limit, ok())
    resilient, sleeps = make(script, now=1_000.0)
    resilient.get(URL)
    assert sleeps == [1.0]


def test_cota_zerada_na_resposta_espera_antes_da_proxima_requisicao():
    script = Script(
        ok(**{"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1060"}), ok(),
    )
    resilient, sleeps = make(script, now=1_000.0)
    resilient.get(URL)
    assert sleeps == []  # a requisição que zerou a cota já foi atendida
    resilient.get(URL)
    assert sleeps == [61.0]
    assert len(script.calls) == 2


def test_cota_do_search_e_independente_da_cota_core():
    script = Script(
        ok(**{"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1060",
              "x-ratelimit-resource": "search"}),
        ok(), ok(),
    )
    resilient, sleeps = make(script, now=1_000.0)
    resilient.get(SEARCH)
    resilient.get(URL)  # core: sem espera
    assert sleeps == []
    resilient.get(SEARCH)
    assert sleeps == [61.0]


def test_rate_limit_persistente_interrompe_sem_loop_infinito():
    limit = ApiError(429, URL, {"retry-after": "1"})
    script = Script(*[limit for _ in range(3)])
    resilient, sleeps = make(script, max_rate_limit_waits=2)
    with pytest.raises(RateLimitExhausted):
        resilient.get(URL)
    assert len(sleeps) == 2


def test_notifica_espera_sem_expor_url_com_segredo():
    messages = []
    script = Script(ApiError(500, URL), ok())
    resilient, _ = make(script, notify=messages.append)
    resilient.get(URL)
    assert messages and "500" in messages[0]


@pytest.mark.parametrize("kwargs", [
    {"max_retries": -1}, {"base_delay": 0}, {"base_delay": 5, "max_delay": 1},
])
def test_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        ResilientTransport(Script(), **kwargs)
