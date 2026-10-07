"""#95: rate limit e retentativas com backoff exponencial como decorador de Transport.

Pilha usada pela CLI: SQLiteCacheTransport -> ResilientTransport -> HttpTransport.
Respostas em cache nunca consomem cota nem passam por aqui.
"""

import time
from typing import Callable
from urllib.parse import urlsplit

from lab03.github import ApiError, NetworkError, Response, Transport

# Segundos extras após X-RateLimit-Reset, para absorver diferença de relógio.
RESET_MARGIN_SECONDS = 1.0
# Espera quando o GitHub sinaliza limite secundário sem Retry-After/Reset.
SECONDARY_LIMIT_FALLBACK_SECONDS = 60.0


class RateLimitExhausted(RuntimeError):
    """Cota esgotada repetidamente; a coleta para sem produzir dados parciais."""


def _int_header(headers: dict[str, str], name: str) -> int | None:
    value = headers.get(name)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _resource(url: str, headers: dict[str, str]) -> str:
    declared = headers.get("x-ratelimit-resource")
    if declared:
        return declared
    return "search" if urlsplit(url).path.startswith("/search") else "core"


class ResilientTransport:
    def __init__(
        self,
        transport: Transport,
        *,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_rate_limit_waits: int = 20,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        notify: Callable[[str], None] | None = None,
    ):
        if max_retries < 0 or base_delay <= 0 or max_delay < base_delay:
            raise ValueError("Parâmetros de retentativa inválidos.")
        self.transport = transport
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_rate_limit_waits = max_rate_limit_waits
        self._sleep = sleep
        self._clock = clock
        self._notify = notify
        # resource -> (remaining, reset epoch) da última resposta observada.
        self._quota: dict[str, tuple[int, int | None]] = {}
        self.retries = 0
        self.rate_limit_waits = 0
        self.waited_seconds = 0.0

    def get(self, url: str) -> Response:
        attempt = 0
        rate_limit_waits = 0
        while True:
            self._wait_for_quota(_resource(url, {}))
            try:
                response = self.transport.get(url)
            except ApiError as error:
                wait = self._rate_limit_wait(error)
                if wait is not None:
                    rate_limit_waits += 1
                    if rate_limit_waits > self.max_rate_limit_waits:
                        raise RateLimitExhausted(
                            "Rate limit persistente; interrompa e rode novamente "
                            "para retomar do cache."
                        ) from None
                    self._wait(wait, f"rate limit (HTTP {error.status})")
                    self.rate_limit_waits += 1
                    continue
                if error.status >= 500 and attempt < self.max_retries:
                    self._backoff(attempt, f"HTTP {error.status}")
                    attempt += 1
                    continue
                raise
            except NetworkError:
                if attempt < self.max_retries:
                    self._backoff(attempt, "falha de rede")
                    attempt += 1
                    continue
                raise
            self._record(url, response.headers)
            return response

    def _record(self, url: str, headers: dict[str, str]) -> None:
        remaining = _int_header(headers, "x-ratelimit-remaining")
        if remaining is not None:
            self._quota[_resource(url, headers)] = (
                remaining, _int_header(headers, "x-ratelimit-reset"),
            )

    def _wait_for_quota(self, resource: str) -> None:
        remaining, reset = self._quota.get(resource, (1, None))
        if remaining > 0:
            return
        # Cota conhecida como zerada: esperar antes de gastar uma requisição.
        del self._quota[resource]
        if reset is not None:
            delay = reset - self._clock() + RESET_MARGIN_SECONDS
            if delay > 0:
                self._wait(delay, f"cota {resource} esgotada")
                self.rate_limit_waits += 1

    def _rate_limit_wait(self, error: ApiError) -> float | None:
        headers = error.headers
        retry_after = _int_header(headers, "retry-after")
        exhausted = _int_header(headers, "x-ratelimit-remaining") == 0
        if error.status not in (403, 429):
            return None
        if retry_after is not None:
            return float(retry_after) + RESET_MARGIN_SECONDS
        if exhausted:
            reset = _int_header(headers, "x-ratelimit-reset")
            if reset is not None:
                return max(reset - self._clock(), 0.0) + RESET_MARGIN_SECONDS
        if error.status == 429:
            return SECONDARY_LIMIT_FALLBACK_SECONDS
        # 403 sem sinal de limite é permissão/autenticação: não repetir.
        return None

    def _backoff(self, attempt: int, reason: str) -> None:
        delay = min(self.base_delay * 2 ** attempt, self.max_delay)
        self.retries += 1
        self._wait(delay, f"{reason}; tentativa {attempt + 2}")

    def _wait(self, seconds: float, reason: str) -> None:
        self.waited_seconds += seconds
        if self._notify:
            self._notify(f"Aguardando {seconds:.0f}s: {reason}.")
        self._sleep(seconds)
