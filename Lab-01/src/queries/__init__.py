"""Strings de query GraphQL: "o que perguntar" pra API do GitHub, uma constante por RQ.

A mecânica de execução (autenticação, request, retry) fica em `src.github_client`;
"o que fazer com a resposta" (extrair/calcular o valor de cada RQ) fica em
`src.metrics`. Todas usam a mesma sintaxe de busca por estrelas (`stars:>1
sort:stars-desc`), que a paginação para 1000 repositórios (Lab01S02) vai
reaproveitar em escala.
"""

BUSCA_POR_ESTRELAS = "stars:>1 sort:stars-desc"

QUERY_RQ01_IDADE = """
query AmostraRQ01($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        createdAt
      }
    }
  }
}
"""

QUERY_RQ02_PRS_ACEITAS = """
query AmostraRQ02($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        pullRequests(states: MERGED) {
          totalCount
        }
      }
    }
  }
}
"""

QUERY_RQ03_RELEASES = """
query AmostraRQ03($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        releases {
          totalCount
        }
      }
    }
  }
}
"""

QUERY_RQ04_ATUALIZACAO = """
query AmostraRQ04($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        pushedAt
      }
    }
  }
}
"""

QUERY_RQ05_LINGUAGEM = """
query($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        primaryLanguage {
          name
        }
      }
    }
  }
}
"""

QUERY_RQ06_ISSUES = """
query($sampleSize: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $sampleSize) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        issues_total: issues {
          totalCount
        }
        issues_closed: issues(states: CLOSED) {
          totalCount
        }
      }
    }
  }
}
"""

# Script único do grupo (Lab01S01) - junta os campos das 6 RQs já integradas
# (RQ01-RQ06; RQ07 é derivada, sem campo próprio - ver scripts/rq07_analise.py).
#
# Usa $pageSize/$after (não $totalRepos/first fixo) porque pedir tudo de uma vez
# (first: 100) com esses campos aninhados (releases, pullRequests, issues) estoura
# o limite de complexidade da API e devolve 502 - paginar em blocos menores
# contorna isso. O tamanho seguro do bloco cai conforme mais campos aninhados são
# adicionados (testado: com as 6 RQs integradas, 40 funciona e 50 já dá 502) -
# ver PAGE_SIZE em `scripts/script_unico_grupo.py`. Ver `src.github_client.paginate()`.
#
# Inclui `rateLimit` (campo irmão de `search`, não aninhado nela) para que quem pagina
# em lote grande (Lab01S02, `paginate_resumable()`) saiba o orçamento restante e possa
# pausar de propósito antes de a API cortar. Scripts que não olham esse campo (o da
# S01) simplesmente ignoram o dado extra - não quebra nada.
QUERY_UNICO_S01 = """
query ConsultaUnicaS01($pageSize: Int!, $after: String) {
  rateLimit {
    remaining
    resetAt
  }
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $pageSize, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount

        # RQ01 - idade (gustavoprehl)
        createdAt

        # RQ02 - PRs aceitas (gustavoprehl)
        pullRequests(states: MERGED) {
          totalCount
        }

        # RQ03 - total de releases (lucasrsnd)
        releases {
          totalCount
        }

        # RQ04 - tempo ate ultima atualizacao (lucasrsnd)
        pushedAt

        # RQ05 - linguagem primaria (DaviSantos23)
        primaryLanguage { 
          name 
        }

        # RQ06 - percentual de issues fechadas (DaviSantos23)
        issues_total: issues { 
          totalCount 
        }
        issues_closed: issues(states: CLOSED) { 
          totalCount 
        }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# ADIÇÃO S02
# ---------------------------------------------------------------------------

# Snapshot do GitHub Projects (v2) para CSV - Enunciado_Lab-01.md, Parte 2, item 6.
# Usa `user(login: ...)` (não `organization`) porque o Project é de conta pessoal.
QUERY_PROJECT_SNAPSHOT_USER = """
query SnapshotProject($login: String!, $number: Int!, $pageSize: Int!, $after: String) {
  user(login: $login) {
    projectV2(number: $number) {
      title
      items(first: $pageSize, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          status: fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
          content {
            ... on Issue {
              number
              title
              url
              state
              assignees(first: 5) {
                nodes {
                  login
                }
              }
            }
            ... on PullRequest {
              number
              title
              url
              state
            }
            ... on DraftIssue {
              title
            }
          }
        }
      }
    }
  }
}
"""
