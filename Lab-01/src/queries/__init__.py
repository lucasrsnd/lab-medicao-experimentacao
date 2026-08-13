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

# Script único do grupo (Lab01S01) - junta os campos das RQs já integradas.
# RQ05/RQ06 continuam TODO (comentadas) até quem for responsável integrar.
#
# KNOWN ISSUE (achado ao testar, responsabilidade de quem tocar a Issue de
# integração de novo): pedir first: 100 aqui (com os campos aninhados
# pullRequests/releases) está retornando 502 da API do GitHub - funciona até
# first: 50. Precisa de investigação/paginação antes de considerar a Issue fechada.
QUERY_UNICO_S01 = """
query ConsultaUnicaS01($totalRepos: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $totalRepos) {
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
