"""Cliente REST próprio com paginação e transportes intercambiáveis.

A interface Transport permite empilhar cache (#96) e rate limit/retentativas
(#95, ver resilience.py) sem alterar coletores. O adaptador HTTP não decide
política: apenas traduz falhas em ApiError/NetworkError com os cabeçalhos
relevantes, para que a camada acima escolha entre esperar, repetir ou falhar.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Iterator, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com/"


class ApiError(RuntimeError):
    def __init__(self, status: int, url: str, headers: dict[str, str] | None = None):
        self.status = status
        self.url = url
        # Cabeçalhos em minúsculas (retry-after, x-ratelimit-*); nunca o corpo.
        self.headers = headers or {}
        # Não incluir corpo remoto, headers ou token na mensagem.
        super().__init__(f"GitHub HTTP {status}: {urlsplit(url).path}")


class NetworkError(RuntimeError):
    """Falha de transporte (DNS, conexão, timeout); candidata a nova tentativa."""


class DataError(ValueError):
    """Resposta incompleta/inconsistente não pode ser usada como dado válido."""


@dataclass(frozen=True)
class Response:
    data: Any
    headers: dict[str, str]


class Transport(Protocol):
    def get(self, url: str) -> Response: ...


class HttpTransport:
    def __init__(self, token: str, timeout: float = 30):
        self.token = token
        self.timeout = timeout

    def get(self, url: str) -> Response:
        validate_url(url)
        authorization_header = "Bearer " + self.token
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": authorization_header,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "lab03-dora/0.1",
        })
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return Response(json.load(response), {
                    key.lower(): value for key, value in response.headers.items()
                })
        except HTTPError as error:
            raise ApiError(error.code, url, _response_headers(error.headers)) from None
        except (URLError, TimeoutError, ConnectionError):
            raise NetworkError("Falha de rede ao consultar GitHub; nenhuma métrica foi gerada.") from None


def _response_headers(headers) -> dict[str, str]:
    if not headers:
        return {}
    return {key.lower(): value for key, value in headers.items()}


class SnapshotTransport:
    """Reproduz respostas salvas; nunca faz fallback para a rede."""
    def __init__(self, responses: dict[str, dict]):
        self.responses = responses

    def get(self, url: str) -> Response:
        if url not in self.responses:
            raise DataError(f"Resposta ausente no snapshot: {url}")
        item = self.responses[url]
        if item.get("status", 200) != 200:
            raise ApiError(item["status"], url, {
                key.lower(): value for key, value in item.get("headers", {}).items()
            })
        return Response(item["data"], {
            key.lower(): value for key, value in item.get("headers", {}).items()
        })


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "api.github.com"
            or parsed.username or parsed.password):
        raise ValueError("A API e os links de paginação devem usar https://api.github.com.")


class GitHubClient:
    def __init__(self, transport: Transport):
        self.transport = transport

    def pages(self, path: str, params: dict | None = None) -> Iterator[Any]:
        url = urljoin(API_ROOT, path)
        if params:
            url += "?" + urlencode(params)
        seen = set()
        while url:
            validate_url(url)
            if url in seen:
                raise DataError("Ciclo no Link de paginação.")
            seen.add(url)
            response = self.transport.get(url)
            yield response.data
            links = response.headers.get("link", "")
            match = re.search(r'<([^>]+)>\s*;\s*rel="next"', links)
            url = urljoin(url, match[1]) if match else ""

    def get(self, path: str, params: dict | None = None) -> Any:
        return next(self.pages(path, params))

