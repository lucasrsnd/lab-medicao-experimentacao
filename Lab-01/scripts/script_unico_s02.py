"""
Script UNICO do grupo - consulta GraphQL para Lab01S02 (1000 repositorios).

Issue: Implementar paginacao para 1000 repositorios [S02] (#9)

Reaproveita a mesma query integrada da S01 (`QUERY_UNICO_S01`, com as 6 RQs), mas
usa `paginate_resumable()` em vez de `paginate()`: page size adaptativo, checkpoint
em disco (retoma sozinho se cair no meio) e pausa automatica se o rate limit da API
ficar baixo. Ver `Lab-01/docs/sprint1-notas.md` (secao 4) para o histórico de por
que isso é necessário - a Search API do GitHub e instavel sob paginacao profunda, e
100 paginas (1000 repos / ~10 por pagina no pior caso) multiplicam a chance de bater
nisso.

Nao roda em cima do resultado da S01 (`repositorios_s01.*`) - gera seus proprios
arquivos (`repositorios_s02.*`), para manter os dois momentos da sprint rastreaveis.

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .          (instala config/src em modo editavel)
    4) python scripts/script_unico_s02.py
       (se cair no meio, so rodar de novo - retoma sozinho do checkpoint)
"""

from __future__ import annotations

from pathlib import Path

from config import load_github_token

from src.export import salvar_csv, salvar_json
from src.github_client import paginate_resumable
from src.metrics import (
    extract_rq01_idade_anos,
    extract_rq02_prs_aceitas,
    extract_rq03_total_releases,
    extract_rq04_dias_desde_atualizacao,
    extract_rq05_linguagem,
    extract_rq06_razao_issues,
)
from src.queries import QUERY_UNICO_S01

TOTAL_REPOS = 1000  # Lab01S02 pede consulta para 1000 repositorios (teto da Search API)
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
CHECKPOINT_PATH = DATA_DIR / ".checkpoint_s02.json"

CAMPOS_CSV = [
    "nameWithOwner",
    "stargazerCount",
    "createdAt",
    "idade_anos",
    "prs_aceitas",
    "total_releases",
    "pushedAt",
    "dias_desde_atualizacao",
    "linguagem_primaria",
    "total_issues",
    "issues_fechadas",
    "razao_fechadas",
]


def buscar_repositorios(token: str) -> list[dict]:
    nodes = paginate_resumable(
        QUERY_UNICO_S01,
        {},
        token,
        total=TOTAL_REPOS,
        checkpoint_path=CHECKPOINT_PATH,
        timeout=60,
    )

    repos = []
    for node in nodes:
        node["idade_anos"] = extract_rq01_idade_anos(node)

        node["prs_aceitas"] = extract_rq02_prs_aceitas(node)
        node.pop("pullRequests", None)

        node["total_releases"] = extract_rq03_total_releases(node)
        node.pop("releases", None)

        node["dias_desde_atualizacao"] = extract_rq04_dias_desde_atualizacao(node)

        node["linguagem_primaria"] = extract_rq05_linguagem(node)
        node.pop("primaryLanguage", None)

        total, closed, razao = extract_rq06_razao_issues(node)
        node["total_issues"] = total
        node["issues_fechadas"] = closed
        node["razao_fechadas"] = razao
        node.pop("issues_total", None)
        node.pop("issues_closed", None)

        repos.append(node)
    return repos


def main() -> None:
    token = load_github_token()
    repos = buscar_repositorios(token)

    print(f"\nConsulta unica S02 - {len(repos)} repositorio(s) coletados (paginado, sem intervencao manual).")

    caminho_json = salvar_json(repos, DATA_DIR / "repositorios_s02.json")
    print(f"Resultado bruto salvo em: {caminho_json}")

    caminho_csv = salvar_csv(repos, CAMPOS_CSV, DATA_DIR / "repositorios_s02.csv")
    print(f"Resultado salvo em: {caminho_csv}")


if __name__ == "__main__":
    main()
