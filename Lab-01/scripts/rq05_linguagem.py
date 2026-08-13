"""
RQ05 - Sistemas populares são escritos nas linguagens mais populares?
Metrica: linguagem primária de cada repositório (primaryLanguage.name).

Issue: RQ05 - extracao e validacao (Linguagem primária) [sprint:S01]

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .
    4) python scripts/rq05_linguagem.py
"""

from __future__ import annotations
from pathlib import Path

from _validacao import validar_amostra_nao_vazia, validar_campo_presente
from config import load_github_token
from src.export import salvar_csv
from src.github_client import run_query

# Em src/queries.py defina QUERY_RQ05_LINGUAGEM buscando primaryLanguage { name }
from src.queries import QUERY_RQ05_LINGUAGEM 

SAMPLE_SIZE = 10
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

def extract_rq05_linguagem(repo: dict) -> str:
    lang_node = repo.get("primaryLanguage")
    if lang_node and isinstance(lang_node, dict):
        return lang_node.get("name", "N/A")
    return "N/A"

def buscar_amostra(token: str) -> list[dict]:
    data = run_query(QUERY_RQ05_LINGUAGEM, {"sampleSize": SAMPLE_SIZE}, token)
    repos = data["search"]["nodes"]
    for repo in repos:
        repo["linguagem_primaria"] = extract_rq05_linguagem(repo)
        repo.pop("primaryLanguage", None)
    return repos

def validar(repos: list[dict]) -> list[str]:
    return (
        validar_amostra_nao_vazia(repos)
        + validar_campo_presente(repos, "linguagem_primaria")
    )

def main() -> None:
    token = load_github_token()
    repos = buscar_amostra(token)
    problemas = validar(repos)

    print(f"\nAmostra RQ05 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'linguagem_primaria':>20}")
    for repo in repos:
        print(f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} {repo['linguagem_primaria']:>20}")

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        raise SystemExit(1)
    print("  [OK] linguagem_primaria presente para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(
        repos,
        ["nameWithOwner", "stargazerCount", "linguagem_primaria"],
        DATA_DIR / "rq05_sample.csv",
    )
    print(f"\nResultado salvo em: {caminho_csv}")

if __name__ == "__main__":
    main()