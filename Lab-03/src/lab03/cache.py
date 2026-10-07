"""#96: transporte com cache SQLite persistente para retomada de coletas.

Cada resposta bem-sucedida é gravada (e confirmada) antes de ser devolvida,
então uma interrupção por Ctrl+C, queda de rede ou rate limit perde no máximo
a requisição em andamento; rodar de novo só consulta a API para o que falta.
Também persiste erros permanentes (404/410/451): os coletores os tratam como
exclusão esperada e repeti-los só gastaria cota. Erros transitórios, de
autenticação e de rate limit nunca são gravados.
"""

import json
import sqlite3
from pathlib import Path

from lab03.github import ApiError, Response, Transport

PERMANENT_ERRORS = frozenset({404, 410, 451})
KEPT_HEADERS = frozenset({
    "link", "etag", "last-modified", "x-ratelimit-remaining", "x-ratelimit-reset",
})


class SQLiteCacheTransport:
    def __init__(self, transport: Transport, path: Path):
        self.transport = transport
        self.path = path
        self.hits = 0
        self.misses = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                url TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                headers TEXT NOT NULL,
                status INTEGER NOT NULL DEFAULT 200
            )
            """
        )
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(responses)")}
        if "status" not in columns:  # cache criado antes do #96
            self.connection.execute(
                "ALTER TABLE responses ADD COLUMN status INTEGER NOT NULL DEFAULT 200"
            )
        self.connection.commit()

    def get(self, url: str) -> Response:
        cached = self._lookup(url)
        if cached is not None:
            self.hits += 1
            status, response = cached
            if status != 200:
                raise ApiError(status, url, response.headers)
            return response

        self.misses += 1
        try:
            response = self.transport.get(url)
        except ApiError as error:
            if error.status in PERMANENT_ERRORS:
                self._store(url, error.status, None, error.headers)
            raise
        headers = self._kept(response.headers)
        self._store(url, 200, response.data, headers)
        return Response(response.data, headers)

    def __len__(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0]

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SQLiteCacheTransport":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    @staticmethod
    def _kept(headers: dict[str, str]) -> dict[str, str]:
        return {k.lower(): v for k, v in headers.items() if k.lower() in KEPT_HEADERS}

    def _lookup(self, url: str) -> tuple[int, Response] | None:
        row = self.connection.execute(
            "SELECT data, headers, status FROM responses WHERE url = ?", (url,),
        ).fetchone()
        if row is None:
            return None
        try:
            return row[2], Response(json.loads(row[0]), json.loads(row[1]))
        except json.JSONDecodeError:
            # Linha corrompida (ex.: disco cheio): tratar como ausente e refazer.
            self.connection.execute("DELETE FROM responses WHERE url = ?", (url,))
            self.connection.commit()
            return None

    def _store(self, url: str, status: int, data, headers: dict[str, str]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO responses (url, data, headers, status) VALUES (?, ?, ?, ?)",
            (
                url,
                json.dumps(data, ensure_ascii=False),
                json.dumps(self._kept(headers), ensure_ascii=False),
                status,
            ),
        )
        self.connection.commit()
