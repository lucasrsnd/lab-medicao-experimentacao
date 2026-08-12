"""
RQ03 - Sistemas populares lancam releases com frequencia?
Metrica: total de releases de cada repositorio (releases.totalCount).

Issue: RQ03 - extracao e validacao (total de releases) [sprint:S01]

Runner: orquestra config (token) + src.queries (o que perguntar) + src.github_client
(como perguntar) + src.metrics (o que fazer com a resposta) + _validacao (conferir)
+ src.export (persistir). Amostra de 5-10 repos, antes de integrar ao script unico
do grupo (script_unico_grupo.py).

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .          (instala config/src em modo editavel)
    4) python scripts/rq03_releases.py
"""

from __future__ import annotations

from pathlib import Path

from _validacao import validar_amostra_nao_vazia, validar_campo_nao_negativo, validar_campo_presente
from config import load_github_token

from src.export import salvar_csv
from src.github_client import run_query
from src.metrics import extract_rq03_total_releases
from src.queries import QUERY_RQ03_RELEASES

SAMPLE_SIZE = 10  # enunciado pede validacao numa amostra de 5-10 repositorios
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def buscar_amostra(token: str) -> list[dict]:
    data = run_query(QUERY_RQ03_RELEASES, {"sampleSize": SAMPLE_SIZE}, token)
    repos = data["search"]["nodes"]
    for repo in repos:
        repo["total_releases"] = extract_rq03_total_releases(repo)
        repo.pop("releases", None)
    return repos


def validar(repos: list[dict]) -> list[str]:
    return (
        validar_amostra_nao_vazia(repos)
        + validar_campo_presente(repos, "total_releases")
        + validar_campo_nao_negativo(repos, "total_releases")
    )


def main() -> None:
    token = load_github_token()
    repos = buscar_amostra(token)
    problemas = validar(repos)

    print(f"\nAmostra RQ03 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'total releases':>15}")
    for repo in repos:
        print(f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} {repo['total_releases']:>15}")

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        raise SystemExit(1)
    print("  [OK] total_releases presente e consistente para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(
        repos,
        ["nameWithOwner", "stargazerCount", "total_releases"],
        DATA_DIR / "rq03_sample.csv",
    )
    print(f"\nResultado salvo em: {caminho_csv}")


if __name__ == "__main__":
    main()
