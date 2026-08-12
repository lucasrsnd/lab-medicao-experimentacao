"""
RQ04 - Sistemas populares sao atualizados com frequencia?
Metrica: tempo ate a ultima atualizacao, calculado a partir de pushedAt (ultimo push).

Issue: RQ04 - extracao e validacao (tempo ate ultima atualizacao) [sprint:S01]

Runner: orquestra config (token) + src.queries (o que perguntar) + src.github_client
(como perguntar) + src.metrics (o que fazer com a resposta) + _validacao (conferir)
+ src.export (persistir). Amostra de 5-10 repos, antes de integrar ao script unico
do grupo (script_unico_grupo.py).

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .          (instala config/src em modo editavel)
    4) python scripts/rq04_atualizacao.py
"""

from __future__ import annotations

from pathlib import Path

from _validacao import validar_amostra_nao_vazia, validar_campo_nao_negativo, validar_campo_presente
from config import load_github_token

from src.export import salvar_csv
from src.github_client import run_query
from src.metrics import extract_rq04_dias_desde_atualizacao
from src.queries import QUERY_RQ04_ATUALIZACAO

SAMPLE_SIZE = 10  # enunciado pede validacao numa amostra de 5-10 repositorios
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def buscar_amostra(token: str) -> list[dict]:
    data = run_query(QUERY_RQ04_ATUALIZACAO, {"sampleSize": SAMPLE_SIZE}, token)
    repos = data["search"]["nodes"]
    for repo in repos:
        repo["dias_desde_atualizacao"] = extract_rq04_dias_desde_atualizacao(repo)
    return repos


def validar(repos: list[dict]) -> list[str]:
    return (
        validar_amostra_nao_vazia(repos)
        + validar_campo_presente(repos, "pushedAt")
        + validar_campo_nao_negativo(repos, "dias_desde_atualizacao")
    )


def main() -> None:
    token = load_github_token()
    repos = buscar_amostra(token)
    problemas = validar(repos)

    print(f"\nAmostra RQ04 - {len(repos)} repositorio(s):\n")
    print(f"{'repositorio':40} {'estrelas':>10} {'ultimo push':>22} {'dias atras':>11}")
    for repo in repos:
        print(
            f"{repo['nameWithOwner']:40} {repo['stargazerCount']:>10} "
            f"{repo['pushedAt']:>22} {repo.get('dias_desde_atualizacao', 'N/A'):>11}"
        )

    print("\nValidacao:")
    if problemas:
        for p in problemas:
            print(f"  [FALHOU] {p}")
        raise SystemExit(1)
    print("  [OK] pushedAt presente e dias desde atualizacao calculados para todos os repositorios da amostra.")

    caminho_csv = salvar_csv(
        repos,
        ["nameWithOwner", "stargazerCount", "pushedAt", "dias_desde_atualizacao"],
        DATA_DIR / "rq04_sample.csv",
    )
    print(f"\nResultado salvo em: {caminho_csv}")


if __name__ == "__main__":
    main()
