"""
RQ02 - Sistemas populares recebem muita contribuicao externa?
Metrica: total de pull requests aceitas (merged).

Issue: RQ02 - extracao e validacao (PRs aceitas) [sprint:S01]

Este script roda uma consulta GraphQL de AMOSTRA (poucos repositorios, ordenados por
estrelas) so para validar o campo/metrica antes de integrar ao script unico do grupo
(Issue "Integrar extracoes individuais no script unico de consulta GraphQL").
Nao faz paginacao para 1000 repositorios ainda - isso e escopo de outra Issue (S02).

Uso:
    1) copie Lab-01/.env.example para Lab-01/.env e preencha GITHUB_TOKEN
       (ja deve existir se voce rodou a RQ01 antes)
    2) pip install -r Lab-01/requirements.txt
    3) python rq02_prs_aceitas.py
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

GRAPHQL_URL = "https://api.github.com/graphql"
SAMPLE_SIZE = 10  # enunciado pede validacao numa amostra de 5-10 repositorios

# Mesma sintaxe de busca (stars:>1 sort:stars-desc) que a Issue de paginacao (S02)
# vai reaproveitar em escala para os 1000 repositorios.
QUERY = """
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


def carregar_token() -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path)
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit(
            f"GITHUB_TOKEN nao encontrado. Copie {env_path.parent / '.env.example'} "
            f"para {env_path} e preencha com um token seu."
        )
    return token


def rodar_query(token: str, sample_size: int) -> list[dict]:
    resposta = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"sampleSize": sample_size}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    if "errors" in corpo:
        sys.exit(f"A API do GitHub retornou erro(s): {corpo['errors']}")
    nodes = corpo["data"]["search"]["nodes"]
    for repo in nodes:
        repo["prs_aceitas"] = repo["pullRequests"]["totalCount"]
        del repo["pullRequests"]
    return nodes


def validar(repos: list[dict]) -> list[str]:
    """Validacoes basicas na amostra. Retorna lista de problemas encontrados (vazia = tudo ok)."""
    problemas = []
    if len(repos) == 0:
        problemas.append("Amostra veio vazia - verifique o token/rate limit.")
    for repo in repos:
        nome = repo.get("nameWithOwner", "<sem nome>")
        if repo.get("prs_aceitas") is None:
            problemas.append(f"{nome}: prs_aceitas ausente/nulo")
        elif repo["prs_aceitas"] < 0:
            problemas.append(f"{nome}: total de PRs aceitas negativo ({repo['prs_aceitas']})")
    return problemas


def salvar_csv(repos: list[dict]) -> Path:
    saida_dir = Path(__file__).parent / "output"
    saida_dir.mkdir(exist_ok=True)
    caminho = saida_dir / "rq02_sample.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nameWithOwner", "stargazerCount", "prs_aceitas"])
        writer.writeheader()
        writer.writerows(repos)
    return caminho


def main() -> None:
    token = carregar_token()
    repos = rodar_query(token, SAMPLE_SIZE)
    problemas = validar(repos)

    print(f"\nAmostra RQ02 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'PRs aceitas':>13}")
    for repo in repos:
        print(f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} {repo['prs_aceitas']:>13}")

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        sys.exit(1)
    print("  [OK] prs_aceitas presente e nao-negativo para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(repos)
    print(f"\nResultado salvo em: {caminho_csv} (nao versionado, so para conferencia local)")


if __name__ == "__main__":
    main()
