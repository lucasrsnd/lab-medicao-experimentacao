"""
RQ06 - Sistemas populares possuem um alto percentual de issues fechadas?
Metrica: razao entre issues fechadas e total de issues.

Issue: RQ06 - extracao e validacao (Taxa de issues fechadas) [sprint:S01]

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .
    4) python scripts/rq06_issues.py
"""

from __future__ import annotations
from pathlib import Path

from _validacao import validar_amostra_nao_vazia, validar_campo_nao_negativo, validar_campo_presente
from config import load_github_token
from src.export import salvar_csv
from src.github_client import run_query

# Em src/queries.py defina QUERY_RQ06_ISSUES buscando issues_total e issues_closed
from src.queries import QUERY_RQ06_ISSUES 

SAMPLE_SIZE = 10
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

def extract_rq06_razao_issues(repo: dict) -> tuple[int, int, float]:
    total = repo.get("issues_total", {}).get("totalCount", 0)
    closed = repo.get("issues_closed", {}).get("totalCount", 0)
    razao = round(closed / total, 4) if total > 0 else 0.0
    return total, closed, razao

def buscar_amostra(token: str) -> list[dict]:
    data = run_query(QUERY_RQ06_ISSUES, {"sampleSize": SAMPLE_SIZE}, token)
    repos = data["search"]["nodes"]
    for repo in repos:
        total, closed, razao = extract_rq06_razao_issues(repo)
        repo["total_issues"] = total
        repo["issues_fechadas"] = closed
        repo["razao_fechadas"] = razao
        repo.pop("issues_total", None)
        repo.pop("issues_closed", None)
    return repos

def validar(repos: list[dict]) -> list[str]:
    return (
        validar_amostra_nao_vazia(repos)
        + validar_campo_presente(repos, "razao_fechadas")
        + validar_campo_nao_negativo(repos, "razao_fechadas")
    )

def main() -> None:
    token = load_github_token()
    repos = buscar_amostra(token)
    problemas = validar(repos)

    print(f"\nAmostra RQ06 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'total':>8} {'fechadas':>10} {'razao':>8}")
    for r in repos:
        print(f"{r['nameWithOwner']:40} {r['stargazerCount']:>10} {r['total_issues']:>8} {r['issues_fechadas']:>10} {r['razao_fechadas']:>8.2f}")

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        raise SystemExit(1)
    print("  [OK] razao de issues tratada contra divisao por zero para todos os repositorios.")

    caminho_csv = salvar_csv(
        repos,
        ["nameWithOwner", "stargazerCount", "total_issues", "issues_fechadas", "razao_fechadas"],
        DATA_DIR / "rq06_sample.csv",
    )
    print(f"\nResultado salvo em: {caminho_csv}")

if __name__ == "__main__":
    main()