"""
RQ01 - Sistemas populares sao maduros/antigos?
Metrica: idade do repositorio, calculada a partir da data de criacao (createdAt).

Issue: RQ01 - extracao e validacao (idade do repositorio) [sprint:S01]

Este script roda uma consulta GraphQL de AMOSTRA (poucos repositorios, ordenados por
estrelas) so para validar o campo/metrica antes de integrar ao script unico do grupo
(Issue "Integrar extracoes individuais no script unico de consulta GraphQL").
Nao faz paginacao para 1000 repositorios ainda - isso e escopo de outra Issue (S02).

Uso:
    1) copie Lab-01/.env.example para Lab-01/.env e preencha GITHUB_TOKEN
    2) pip install -r Lab-01/requirements.txt
    3) python rq01_idade.py
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
SAMPLE_SIZE = 10  # enunciado pede validacao numa amostra de 5-10 repositorios

# Mesma sintaxe de busca (stars:>1 sort:stars-desc) que a Issue de paginacao (S02)
# vai reaproveitar em escala para os 1000 repositorios.
QUERY = """
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
    return corpo["data"]["search"]["nodes"]


def calcular_idade_anos(created_at: str) -> float:
    criado_em = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    agora = datetime.now(timezone.utc)
    dias = (agora - criado_em).days
    return round(dias / 365.25, 2)


def validar(repos: list[dict]) -> list[str]:
    """Validacoes basicas na amostra. Retorna lista de problemas encontrados (vazia = tudo ok)."""
    problemas = []
    if len(repos) == 0:
        problemas.append("Amostra veio vazia - verifique o token/rate limit.")
    for repo in repos:
        nome = repo.get("nameWithOwner", "<sem nome>")
        if not repo.get("createdAt"):
            problemas.append(f"{nome}: createdAt ausente/nulo")
            continue
        idade = calcular_idade_anos(repo["createdAt"])
        if idade < 0:
            problemas.append(f"{nome}: idade calculada negativa ({idade}) - checar timezone/parse")
        repo["idade_anos"] = idade
    return problemas


def salvar_csv(repos: list[dict]) -> Path:
    saida_dir = Path(__file__).parent / "output"
    saida_dir.mkdir(exist_ok=True)
    caminho = saida_dir / "rq01_sample.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nameWithOwner", "stargazerCount", "createdAt", "idade_anos"])
        writer.writeheader()
        writer.writerows(repos)
    return caminho


def main() -> None:
    token = carregar_token()
    repos = rodar_query(token, SAMPLE_SIZE)
    problemas = validar(repos)

    print(f"\nAmostra RQ01 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'criado em':>22} {'idade (anos)':>13}")
    for repo in repos:
        print(
            f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} "
            f"{repo['createdAt']:>22} {repo.get('idade_anos', 'N/A'):>13}"
        )

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        sys.exit(1)
    print("  [OK] createdAt presente e idade calculada para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(repos)
    print(f"\nResultado salvo em: {caminho_csv} (nao versionado, so para conferencia local)")


if __name__ == "__main__":
    main()
