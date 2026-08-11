"""
RQ03 - Sistemas populares lancam releases com frequencia?
Metrica: total de releases de cada repositorio (releases.totalCount).

Issue: RQ03 - extracao e validacao (total de releases) [sprint:S01]

Este script roda uma consulta GraphQL de AMOSTRA (poucos repositorios, ordenados por
estrelas) so para validar o campo/metrica antes de integrar ao script unico do grupo
(Issue "Integrar extracoes individuais no script unico de consulta GraphQL").
Nao faz paginacao para 1000 repositorios ainda - isso e escopo de outra Issue (S02).

Uso:
    1) copie Lab-01/.env.example para Lab-01/.env e preencha GITHUB_TOKEN
    2) pip install -r Lab-01/requirements.txt
    3) python rq03_releases.py
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

    # achata releases.totalCount para o topo do dict, facilita validacao/csv
    repos = []
    for node in corpo["data"]["search"]["nodes"]:
        node["total_releases"] = node.get("releases", {}).get("totalCount")
        del node["releases"]
        repos.append(node)
    return repos


def validar(repos: list[dict]) -> list[str]:
    """Validacoes basicas na amostra. Retorna lista de problemas encontrados (vazia = tudo ok)."""
    problemas = []
    if len(repos) == 0:
        problemas.append("Amostra veio vazia - verifique o token/rate limit.")
    for repo in repos:
        nome = repo.get("nameWithOwner", "<sem nome>")
        if repo.get("total_releases") is None:
            problemas.append(f"{nome}: total_releases ausente/nulo")
            continue
        if repo["total_releases"] < 0:
            problemas.append(f"{nome}: total_releases negativo ({repo['total_releases']}) - inconsistente")
    return problemas


def salvar_csv(repos: list[dict]) -> Path:
    saida_dir = Path(__file__).parent / "output"
    saida_dir.mkdir(exist_ok=True)
    caminho = saida_dir / "rq03_sample.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nameWithOwner", "stargazerCount", "total_releases"])
        writer.writeheader()
        writer.writerows(repos)
    return caminho


def main() -> None:
    token = carregar_token()
    repos = rodar_query(token, SAMPLE_SIZE)
    problemas = validar(repos)

    print(f"\nAmostra RQ03 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'total releases':>15}")
    for repo in repos:
        print(f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} {repo['total_releases']:>15}")

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        sys.exit(1)
    print("  [OK] total_releases presente e consistente para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(repos)
    print(f"\nResultado salvo em: {caminho_csv} (nao versionado, so para conferencia local)")


if __name__ == "__main__":
    main()
