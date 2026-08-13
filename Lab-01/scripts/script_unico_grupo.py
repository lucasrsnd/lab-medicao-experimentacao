"""
Script UNICO do grupo - consulta GraphQL para Lab01S01.

Issue: Integrar extracoes individuais no script unico de consulta GraphQL [sprint:S01]

Junta num unico request GraphQL os campos ja validados individualmente por cada
integrante (ver os outros runners em scripts/), evitando 1 requisicao por RQ.

Cobertura atual (marcar [x] conforme cada RQ for integrada por quem e responsavel):
    [x] RQ01 - createdAt                  (gustavoprehl)
    [x] RQ02 - pull requests aceitas       (gustavoprehl)
    [x] RQ03 - releases.totalCount         (lucasrsnd)
    [x] RQ04 - pushedAt                    (lucasrsnd)
    [x] RQ05 - primaryLanguage             (DaviSantos23) 
    [x] RQ06 - issues abertas/fechadas     (DaviSantos23) 
    [x] RQ07 - analise combinatoria        (DaviSantos23)

Ainda SEM paginacao (busca so os 100 primeiros por estrelas, conforme pede o
Lab01S01). Paginacao para 1000 repositorios e escopo do Lab01S02.

KNOWN ISSUE (achado ao testar, responsabilidade de quem tocar esta Issue de novo):
pedir first: 100 nesta query (com os campos aninhados pullRequests/releases) esta
retornando 502 da API do GitHub - funciona ate first: 50. Precisa de investigacao/
paginacao antes de considerar esta Issue fechada.

Uso (a partir de Lab-01/):
    1) copie .env.example para .env e preencha GITHUB_TOKEN
    2) pip install -r requirements.txt
    3) pip install -e .          (instala config/src em modo editavel)
    4) python scripts/script_unico_grupo.py
"""

from __future__ import annotations
from pathlib import Path

from config import load_github_token
from src.export import salvar_csv
from src.github_client import run_query
from src.metrics import (
    extract_rq01_idade_anos,
    extract_rq02_prs_aceitas,
    extract_rq03_total_releases,
    extract_rq04_dias_desde_atualizacao,
    extract_rq05_linguagem,
    extract_rq06_razao_issues,
)
from src.queries import QUERY_UNICO_S01

TOTAL_REPOS = 10
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

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
    data = run_query(QUERY_UNICO_S01, {"totalRepos": TOTAL_REPOS}, token, timeout=60)
    repos = []
    for node in data["search"]["nodes"]:
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

    print(f"Consulta unica S01 - {len(repos)} repositorio(s) coletados.")

    caminho_csv = salvar_csv(repos, CAMPOS_CSV, DATA_DIR / "repositorios_s01.csv")
    print(f"Resultado salvo em: {caminho_csv}")

if __name__ == "__main__":
    main()
