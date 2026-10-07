"""Transporte HTTP com cache SQLite persistente para retomada de coletas."""

import json
import sqlite3
from pathlib import Path

from lab03.github import Response, Transport


class SQLiteCacheTransport:
    def __init__(self, transport: Transport, path: Path):
        self.transport = transport
        self.path = path
        self.hits = 0
        self.misses = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                url TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                headers TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def get(self, url: str) -> Response:
        cached = self.connection.execute(
            "SELECT data, headers FROM responses WHERE url = ?", (url,),
        ).fetchone()
        if cached is not None:
            self.hits += 1
            return Response(json.loads(cached[0]), json.loads(cached[1]))

        self.misses += 1
        response = self.transport.get(url)
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {
                "link", "etag", "last-modified",
                "x-ratelimit-remaining", "x-ratelimit-reset",
            }
        }
        self.connection.execute(
            "INSERT OR REPLACE INTO responses (url, data, headers) VALUES (?, ?, ?)",
            (
                url,
                json.dumps(response.data, ensure_ascii=False),
                json.dumps(headers, ensure_ascii=False),
            ),
        )
        self.connection.commit()
        return Response(response.data, headers)
