"""Servidor HTTP local para o piloto de fumaça do Lab05 (S01-04, #184).

Enquanto o software não é escolhido (#181), o piloto valida o pipeline coleta → análise
contra este servidor, sem enviar nenhuma requisição a terceiros. Dois tratamentos:

- ``/a/<unidade>``: gera a página a cada requisição (trabalho de CPU proporcional à unidade);
- ``/b/<unidade>``: mesma página, servida de um cache em memória após a primeira geração.

Uso (a partir de Lab-05):  python scripts/servidor_local.py --porta 8765
"""

from __future__ import annotations

import argparse
import hashlib
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def gerar_pagina(unidade: str) -> bytes:
    """Página determinística; o custo cresce com o número no fim da unidade (p01…p20)."""
    peso = int("".join(c for c in unidade if c.isdigit()) or "1")
    bloco = unidade.encode()
    for _ in range(2_000 * peso):  # trabalho de CPU, em vez de sleep, para haver variação real
        bloco = hashlib.sha256(bloco).digest()
    corpo = (bloco.hex() + "\n") * (64 * peso)
    return f"<html><body><h1>{unidade}</h1><pre>{corpo}</pre></body></html>".encode()


@lru_cache(maxsize=None)
def pagina_em_cache(unidade: str) -> bytes:
    return gerar_pagina(unidade)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (nome exigido por BaseHTTPRequestHandler)
        partes = self.path.strip("/").split("/")
        if self.path == "/robots.txt":
            self._responder(200, b"User-agent: *\nAllow: /\n", "text/plain")
        elif len(partes) == 2 and partes[0] in ("a", "b") and partes[1]:
            corpo = gerar_pagina(partes[1]) if partes[0] == "a" else pagina_em_cache(partes[1])
            self._responder(200, corpo, "text/html; charset=utf-8")
        else:
            self._responder(404, b"nao encontrado", "text/plain")

    def _responder(self, status: int, corpo: bytes, tipo: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args) -> None:  # silencioso; a coleta já registra tudo
        pass


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--porta", type=int, default=8765)
    args = p.parse_args()
    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    print(f"Servindo em http://127.0.0.1:{args.porta} (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
