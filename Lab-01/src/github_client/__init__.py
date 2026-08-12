"""Cliente HTTP mínimo para a API GraphQL do GitHub.

Sem bibliotecas de terceiros específicas do GitHub (ex.: PyGithub, gql) - só
`requests` puro, conforme exigido pelo enunciado ("a query GraphQL deve ser
escrita e consumida por script próprio do grupo"). Token e URL da API vêm de
`config` (raiz do Lab-01); aqui fica só a mecânica de request/erro/retry.
"""

from __future__ import annotations

import sys
import time

import requests

from config import GRAPHQL_URL

MAX_TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS_S = 2


def run_query(query: str, variables: dict, token: str, timeout: int = 30) -> dict:
    """Executa uma query GraphQL autenticada e devolve o campo `data` da resposta.

    - Erros retornados pela própria API (campo `errors` no corpo) encerram o
      programa na hora - são erro de query/permissão, repetir não ajuda.
    - Falhas de rede/timeout (conexão instável, DNS, etc.) fazem retry simples
      algumas vezes antes de desistir.
    """
    ultimo_erro: Exception | None = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout,
            )
            resposta.raise_for_status()
            corpo = resposta.json()
            if "errors" in corpo:
                sys.exit(f"A API do GitHub retornou erro(s): {corpo['errors']}")
            return corpo["data"]
        except requests.exceptions.RequestException as erro:
            ultimo_erro = erro
            if tentativa < MAX_TENTATIVAS:
                print(
                    f"[aviso] falha de rede (tentativa {tentativa}/{MAX_TENTATIVAS}): "
                    f"{erro}. Tentando de novo..."
                )
                time.sleep(ESPERA_ENTRE_TENTATIVAS_S)
    sys.exit(f"Falha ao consultar a API do GitHub após {MAX_TENTATIVAS} tentativas: {ultimo_erro}")
