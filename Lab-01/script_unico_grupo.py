"""
Script UNICO do grupo - consulta GraphQL para Lab01S01.

Issue: Integrar extracoes individuais no script unico de consulta GraphQL [sprint:S01]

Junta num unico request GraphQL os campos ja validados individualmente por cada
integrante (ver Lab-01/individual/<usuario>/), evitando 1 requisicao por RQ.

Cobertura atual (marcar [x] conforme cada RQ for integrada por quem e responsavel):
    [x] RQ01 - createdAt                  (gustavoprehl)
    [ ] RQ02 - pull requests aceitas       (gustavoprehl)  -> TODO: adicionar campo
    [x] RQ03 - releases.totalCount         (lucasrsnd)
    [x] RQ04 - pushedAt                    (lucasrsnd)
    [ ] RQ05 - primaryLanguage             (terceiro integrante) -> TODO: adicionar campo
    [ ] RQ06 - issues abertas/fechadas     (terceiro integrante) -> TODO: adicionar campo

Ainda SEM paginacao (busca so os 100 primeiros por estrelas, conforme pede o
Lab01S01). Paginacao para 1000 repositorios e escopo do Lab01S02.

Uso:
    1) copie Lab-01/.env.example para Lab-01/.env e preencha GITHUB_TOKEN
    2) pip install -r Lab-01/requirements.txt
    3) python script_unico_grupo.py
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

GRAPHQL_URL = "https://api.github.com/graphql"
TOTAL_REPOS = 100  # Lab01S01 pede consulta para 100 repositorios (sem paginacao ainda)

QUERY = """
query ConsultaUnicaS01($totalRepos: Int!) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $totalRepos) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount

        # RQ01 - idade (gustavoprehl)
        createdAt

        # RQ02 - PRs aceitas (gustavoprehl) - TODO: confirmar campo/estado usado
        # pullRequests(states: MERGED) { totalCount }

        # RQ03 - total de releases (lucasrsnd)
        releases {
          totalCount
        }

        # RQ04 - tempo ate ultima atualizacao (lucasrsnd)
        pushedAt

        # RQ05 - linguagem primaria - TODO: adicionar quando o responsavel integrar
        # primaryLanguage { name }

        # RQ06 - percentual de issues fechadas - TODO: adicionar quando o responsavel integrar
        # issues(states: OPEN) { totalCount }
        # closedIssues: issues(states: CLOSED) { totalCount }
      }
    }
  }
}
"""


def carregar_token() -> str:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit(
            f"GITHUB_TOKEN nao encontrado. Copie {env_path.parent / '.env.example'} "
            f"para {env_path} e preencha com um token seu."
        )
    return token


def rodar_query(token: str, total_repos: int) -> list[dict]:
    resposta = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"totalRepos": total_repos}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    if "errors" in corpo:
        sys.exit(f"A API do GitHub retornou erro(s): {corpo['errors']}")

    repos = []
    for node in corpo["data"]["search"]["nodes"]:
        node["total_releases"] = node.get("releases", {}).get("totalCount")
        node.pop("releases", None)
        repos.append(node)
    return repos


def calcular_derivados(repos: list[dict]) -> None:
    """Calcula campos derivados (idade, dias desde atualizacao) in-place."""
    agora = datetime.now(timezone.utc)
    for repo in repos:
        if repo.get("createdAt"):
            criado_em = datetime.fromisoformat(repo["createdAt"].replace("Z", "+00:00"))
            repo["idade_anos"] = round((agora - criado_em).days / 365.25, 2)
        if repo.get("pushedAt"):
            atualizado_em = datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00"))
            repo["dias_desde_atualizacao"] = (agora - atualizado_em).days


def salvar_csv(repos: list[dict]) -> Path:
    saida_dir = Path(__file__).parent / "output"
    saida_dir.mkdir(exist_ok=True)
    caminho = saida_dir / "repositorios_s01.csv"
    campos = [
        "nameWithOwner",
        "stargazerCount",
        "createdAt",
        "idade_anos",
        "total_releases",
        "pushedAt",
        "dias_desde_atualizacao",
    ]
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(repos)
    return caminho


def main() -> None:
    token = carregar_token()
    repos = rodar_query(token, TOTAL_REPOS)
    calcular_derivados(repos)

    print(f"Consulta unica S01 - {len(repos)} repositorio(s) coletados.")

    caminho_csv = salvar_csv(repos)
    print(f"Resultado salvo em: {caminho_csv}")
    print(
        "\nLembrete: RQ02, RQ05 e RQ06 ainda estao marcados como TODO neste script - "
        "cada responsavel deve descomentar/adicionar o campo validado na sua Issue "
        "antes do fechamento da sprint."
    )


if __name__ == "__main__":
    main()
