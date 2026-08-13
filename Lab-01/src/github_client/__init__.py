"""Cliente HTTP mínimo para a API GraphQL do GitHub.

Sem bibliotecas de terceiros específicas do GitHub (ex.: PyGithub, gql) - só
`requests` puro, conforme exigido pelo enunciado ("a query GraphQL deve ser
escrita e consumida por script próprio do grupo"). Token e URL da API vêm de
`config` (raiz do Lab-01); aqui fica só a mecânica de request/erro/retry/paginação.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import GRAPHQL_URL

MAX_TENTATIVAS = 5
ESPERA_ENTRE_TENTATIVAS_S = 3  # com backoff exponencial (3s, 6s, 12s, 24s) - 502 em paginacao
# profunda do `search` costuma ser transiente do lado do GitHub, uma espera maior
# entre tentativas resolve melhor do que insistir rapido
ENTRE_PAGINAS_S = 2  # pausa entre paginas bem-sucedidas, pra nao martelar a API de search

SEARCH_LIMITE_MAXIMO = 1000  # a Search API do GitHub só permite acessar os primeiros
# 1000 resultados, documentado - não adianta pedir mais por este endpoint


class GraphQLTransientError(Exception):
    """Erro de rede/gateway persistente - `run_query` já esgotou seus retries
    internos. Usado por quem faz adaptação em nível mais alto (`paginate_resumable`)
    para reagir (reduzir page_size, etc.) em vez de simplesmente encerrar o programa.
    """


def run_query(
    query: str,
    variables: dict,
    token: str,
    timeout: int = 30,
    *,
    raise_on_failure: bool = False,
) -> dict:
    """Executa uma query GraphQL autenticada e devolve o campo `data` da resposta.

    - Erros retornados pela própria API (campo `errors` no corpo) sempre encerram o
      programa na hora - são erro de query/permissão, repetir não ajuda.
    - Falhas de rede/timeout/gateway (conexão instável, 502, etc.) fazem retry com
      backoff exponencial algumas vezes antes de desistir. Por padrão, desistir
      encerra o programa (`sys.exit`) com uma mensagem clara; passe
      `raise_on_failure=True` para receber uma `GraphQLTransientError` em vez disso
      (uso de quem quer decidir sozinho o que fazer com a falha, ex.: `paginate_resumable`).
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

    mensagem = f"Falha ao consultar a API do GitHub após {MAX_TENTATIVAS} tentativas: {ultimo_erro}"
    if raise_on_failure:
        raise GraphQLTransientError(mensagem) from ultimo_erro
    sys.exit(mensagem)


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

    Versão simples, sem checkpoint nem page_size adaptativo - usada pelo script da
    S01 (100 repositórios). Para lotes grandes (Lab01S02, 1000 repositórios), ver
    `paginate_resumable`.
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


def _ler_checkpoint(caminho: Path, total_esperado: int) -> dict | None:
    if not caminho.exists():
        return None
    try:
        with caminho.open("r", encoding="utf-8") as f:
            checkpoint = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if checkpoint.get("total") != total_esperado:
        print(
            f"[checkpoint] ignorado: foi salvo para total={checkpoint.get('total')}, "
            f"mas pedimos total={total_esperado}. Começando do zero."
        )
        return None
    return checkpoint


def _salvar_checkpoint(caminho: Path, total: int, cursor: str | None, page_size: int, repos: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = {"total": total, "cursor": cursor, "page_size": page_size, "repos": repos}
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(conteudo, f)
    tmp.replace(caminho)  # escrita atomica - evita checkpoint corrompido se cair no meio


def _pausar_se_rate_limit_baixo(data: dict, minimo: int = 50) -> None:
    rate_limit = data.get("rateLimit")
    if not rate_limit:
        return
    restante = rate_limit.get("remaining")
    reset_at = rate_limit.get("resetAt")
    if restante is None or reset_at is None or restante >= minimo:
        return
    reset_em = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
    espera = max((reset_em - datetime.now(timezone.utc)).total_seconds(), 0) + 5  # margem de seguranca
    print(f"[aviso] rate limit baixo ({restante} restantes) - pausando {espera:.0f}s até {reset_at}")
    time.sleep(espera)


def paginate_resumable(
    query: str,
    variables: dict,
    token: str,
    *,
    total: int,
    checkpoint_path: Path,
    page_size_inicial: int = 30,
    page_size_min: int = 5,
    page_size_max: int = 40,
    sucessos_para_subir: int = 5,
    incremento_subida: int = 5,
    max_falhas_seguidas: int = 6,
    timeout: int = 30,
) -> list[dict]:
    """Versão robusta de `paginate()` para lotes grandes (ex.: 1000 repositórios, Lab01S02).

    - **Page size adaptativo** (estilo AIMD): reduz pela metade numa falha
      persistente (piso `page_size_min`), aumenta aos poucos após vários sucessos
      seguidos (teto `page_size_max`).
    - **Checkpoint em disco** (`checkpoint_path`, JSON) a cada página bem-sucedida -
      se o processo for interrompido/falhar, a próxima chamada retoma do cursor
      salvo em vez de recomeçar do zero. Apagado ao concluir com sucesso.
    - **Consciência de rate limit real** (campo `rateLimit` da query, se presente) -
      pausa de propósito antes da API cortar, em vez de só reagir a erro.
    - Loga progresso por página.

    A `query` precisa aceitar `$pageSize`/`$after`, devolver `pageInfo` dentro de
    `search`, e idealmente `rateLimit { remaining resetAt }` (ver
    `src.queries.QUERY_UNICO_S01`).

    Desiste (salvando checkpoint e chamando `sys.exit`) depois de
    `max_falhas_seguidas` páginas seguidas falhando mesmo após reduzir o page_size
    ao mínimo.
    """
    if total > SEARCH_LIMITE_MAXIMO:
        raise ValueError(
            f"A Search API do GitHub só permite acessar os primeiros {SEARCH_LIMITE_MAXIMO} "
            f"resultados - total={total} não é suportado por este endpoint."
        )

    checkpoint = _ler_checkpoint(checkpoint_path, total)
    if checkpoint:
        nodes: list[dict] = checkpoint["repos"]
        cursor: str | None = checkpoint["cursor"]
        page_size = checkpoint["page_size"]
        print(f"[checkpoint] retomando de {len(nodes)}/{total} repos (page_size={page_size})")
    else:
        nodes = []
        cursor = None
        page_size = page_size_inicial

    sucessos_seguidos = 0
    falhas_seguidas = 0

    while len(nodes) < total:
        restantes = total - len(nodes)
        pagina_vars = {**variables, "pageSize": min(page_size, restantes), "after": cursor}

        try:
            data = run_query(query, pagina_vars, token, timeout=timeout, raise_on_failure=True)
        except GraphQLTransientError as erro:
            falhas_seguidas += 1
            sucessos_seguidos = 0
            if falhas_seguidas >= max_falhas_seguidas:
                _salvar_checkpoint(checkpoint_path, total, cursor, page_size, nodes)
                sys.exit(
                    f"Desistindo após {falhas_seguidas} páginas seguidas falhando ({erro}). "
                    f"Progresso salvo em {checkpoint_path} ({len(nodes)}/{total} repositórios) - "
                    f"rode de novo pra retomar."
                )
            page_size = max(page_size // 2, page_size_min)
            print(f"[aviso] página falhou ({erro}). Reduzindo page_size para {page_size} e tentando de novo.")
            time.sleep(ENTRE_PAGINAS_S)
            continue  # tenta de novo o mesmo cursor, com page_size menor

        falhas_seguidas = 0
        _pausar_se_rate_limit_baixo(data)

        pagina = data["search"]
        nodes.extend(pagina["nodes"])
        cursor = pagina["pageInfo"]["endCursor"]
        _salvar_checkpoint(checkpoint_path, total, cursor, page_size, nodes)

        restante_rl = data.get("rateLimit", {}).get("remaining", "?")
        print(
            f"[pagina] +{len(pagina['nodes'])} repos (total {len(nodes)}/{total}) | "
            f"page_size={page_size} | rate_limit={restante_rl}"
        )

        if not pagina["pageInfo"]["hasNextPage"]:
            break

        sucessos_seguidos += 1
        if sucessos_seguidos >= sucessos_para_subir and page_size < page_size_max:
            page_size = min(page_size + incremento_subida, page_size_max)
            sucessos_seguidos = 0

        time.sleep(ENTRE_PAGINAS_S)

    checkpoint_path.unlink(missing_ok=True)  # concluído - remove o estado intermediário
    return nodes[:total]
