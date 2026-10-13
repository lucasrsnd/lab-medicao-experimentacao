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
import threading
from pathlib import Path

from lab03.github import ApiError, Response, Transport

PERMANENT_ERRORS = frozenset({404, 410, 451})
KEPT_HEADERS = frozenset({
    "link", "etag", "last-modified", "x-ratelimit-remaining", "x-ratelimit-reset",
})


RUN_FIELDS = (
    "id", "workflow_id", "name", "head_branch", "event", "status", "conclusion",
    "head_sha", "created_at", "run_started_at", "updated_at",
)
RELEASE_FIELDS = (
    "id", "draft", "prerelease", "published_at", "tag_name", "body", "html_url",
    "target_commitish",
)


def _pick(item, fields):
    return {key: item[key] for key in fields if isinstance(item, dict) and key in item}


def compact(url: str, data):
    """Mantém só os campos que o pipeline lê. Workflow runs, releases e compare
    trazem dezenas de campos (repositório embutido, assets, lista de arquivos)
    que multiplicam o cache por ~10 sem mudar nenhuma métrica."""
    path = url.split("?", 1)[0]
    if path.endswith("/actions/runs") and isinstance(data, dict) and isinstance(
        data.get("workflow_runs"), list
    ):
        return {
            "total_count": data.get("total_count"),
            "workflow_runs": [_pick(run, RUN_FIELDS) for run in data["workflow_runs"]],
        }
    if path.endswith("/releases") and isinstance(data, list):
        return [_pick(release, RELEASE_FIELDS) for release in data]
    if "/compare/" in path and isinstance(data, dict) and isinstance(data.get("commits"), list):
        slim = {key: data[key] for key in ("status", "total_commits") if key in data}
        slim["commits"] = [
            {
                "sha": commit.get("sha"),
                "commit": {
                    "message": (commit.get("commit") or {}).get("message"),
                    "author": _pick((commit.get("commit") or {}).get("author") or {}, ("date",)),
                },
            }
            for commit in data["commits"]
        ]
        return slim
    if "/commits/" in path and isinstance(data, dict) and "sha" in data and "files" in data:
        commit = data.get("commit") or {}
        return {
            "sha": data["sha"],
            "commit": {
                "message": commit.get("message"),
                "author": _pick(commit.get("author") or {}, ("date",)),
            },
        }
    return data


class SQLiteCacheTransport:
    def __init__(self, transport: Transport, path: Path, *, namespace: str = ""):
        self.transport = transport
        self.path = path
        self.namespace = namespace
        self.hits = 0
        self.misses = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
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
        if "fetched_at" not in columns:
            self.connection.execute("ALTER TABLE responses ADD COLUMN fetched_at TEXT")
        self.connection.commit()

    def get(self, url: str) -> Response:
        key = f"{self.namespace}\n{url}" if self.namespace else url
        cached = self._lookup(key)  # a decodificação do JSON fica fora da trava
        if cached is not None:
            with self._lock:
                self.hits += 1
            status, response = cached
            if status != 200:
                raise ApiError(status, url, response.headers)
            return response

        with self._lock:
            self.misses += 1
        try:
            response = self.transport.get(url)
        except ApiError as error:
            if error.status in PERMANENT_ERRORS:
                with self._lock:
                    self._store(key, error.status, None, error.headers)
            raise
        headers = self._kept(response.headers)
        data = compact(url, response.data)
        with self._lock:
            self._store(key, 200, data, headers)
        return Response(data, headers)

    def __len__(self) -> int:
        with self._lock:
            return self.connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def clear(self) -> None:
        """Invalida apenas o snapshot desta configuração; outros ficam intactos."""
        prefix = self.namespace + "\n"
        if self.namespace:
            self.connection.execute(
                "DELETE FROM responses WHERE substr(url, 1, ?) = ?", (len(prefix), prefix),
            )
        else:
            self.connection.execute("DELETE FROM responses WHERE instr(url, char(10)) = 0")
        self.connection.commit()

    def __enter__(self) -> "SQLiteCacheTransport":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    @staticmethod
    def _kept(headers: dict[str, str]) -> dict[str, str]:
        return {k.lower(): v for k, v in headers.items() if k.lower() in KEPT_HEADERS}

    def _lookup(self, url: str) -> tuple[int, Response] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT data, headers, status FROM responses WHERE url = ?", (url,),
            ).fetchone()
        if row is None:
            return None
        try:
            return row[2], Response(json.loads(row[0]), json.loads(row[1]))
        except json.JSONDecodeError:
            # Linha corrompida (ex.: disco cheio): tratar como ausente e refazer.
            with self._lock:
                self.connection.execute("DELETE FROM responses WHERE url = ?", (url,))
                self.connection.commit()
            return None

    def _store(self, url: str, status: int, data, headers: dict[str, str]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO responses (url, data, headers, status, fetched_at) "
            "VALUES (?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
            (
                url,
                json.dumps(data, ensure_ascii=False),
                json.dumps(self._kept(headers), ensure_ascii=False),
                status,
            ),
        )
        self.connection.commit()
