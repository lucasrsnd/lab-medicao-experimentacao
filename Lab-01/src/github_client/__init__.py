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

MAX_TENTATIVAS = 5
ESPERA_ENTRE_TENTATIVAS_S = 3  # com backoff exponencial (3s, 6s, 12s, 24s) - 502 em paginacao
# profunda do `search` costuma ser transiente do lado do GitHub, uma espera maior
# entre tentativas resolve melhor do que insistir rapido
ENTRE_PAGINAS_S = 2  # pausa entre paginas bem-sucedidas, pra nao martelar a API de search


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
                espera = ESPERA_ENTRE_TENTATIVAS_S * (2 ** (tentativa - 1))  # backoff exponencial
                print(
                    f"[aviso] falha de rede (tentativa {tentativa}/{MAX_TENTATIVAS}): "
                    f"{erro}. Tentando de novo em {espera}s..."
                )
                time.sleep(espera)
    sys.exit(f"Falha ao consultar a API do GitHub após {MAX_TENTATIVAS} tentativas: {ultimo_erro}")


def paginate(
    query: str,
    variables: dict,
    token: str,
    *,
    total: int,
    page_size: int,
    timeout: int = 30,
) -> list[dict]:
    """Pagina uma query GraphQL baseada em `search` até coletar `total` nós.

    A query precisa aceitar `$pageSize: Int!` e `$after: String`, e devolver
    `pageInfo { hasNextPage endCursor }` dentro de `search` (ver
    `src.queries.QUERY_UNICO_S01`). `variables` leva as variáveis fixas da query
    (se houver) - `pageSize`/`after` são injetadas aqui a cada página.

    Existe porque pedir tudo de uma vez (`first: 100`) em queries com campos
    aninhados (releases, pullRequests, issues) pode estourar o limite de
    complexidade da API e devolver 502 - buscar em blocos menores contorna isso.
    Além disso, a API de `search` do GitHub tem limite de taxa bem mais baixo e
    instável que o resto da GraphQL API - requisições em sequência rápida podem
    disparar 502 mesmo abaixo do limite de complexidade. Por isso há uma pausa
    curta entre páginas (não na primeira), de propósito, para não martelar a API.
    """
    nodes: list[dict] = []
    cursor: str | None = None
    primeira_pagina = True
    while len(nodes) < total:
        if not primeira_pagina:
            time.sleep(ENTRE_PAGINAS_S)
        primeira_pagina = False

        restantes = total - len(nodes)
        pagina_vars = {**variables, "pageSize": min(page_size, restantes), "after": cursor}
        data = run_query(query, pagina_vars, token, timeout=timeout)
        pagina = data["search"]
        nodes.extend(pagina["nodes"])
        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]
    return nodes[:total]
