"""
Snapshot de fechamento de sprint do GitHub Projects -> CSV [S02]

Issue: Script de snapshot GraphQL do Project -> CSV + rodar 1o snapshot [sprint:S02]

Como o GitHub Projects (v2) nao guarda historico de mudanca de coluna consultavel
via API (Enunciado_Lab-01.md, Parte 2, item 6), esse script tira uma "foto" do
board no momento em que roda: cada item (Issue), o status atual (coluna) e o(s)
responsavel(is). Rodar de novo ao final de cada sprint acumula uma serie de
snapshots que serve de base para os Labs 04 e 05.

Uso (a partir de Lab-01/):
    1) preencha no .env: GITHUB_TOKEN, GITHUB_PROJECT_OWNER e GITHUB_PROJECT_NUMBER
    2) python scripts/snapshot_project.py --sprint S02
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from config import load_github_token, load_project_config

from src.github_client import run_query
from src.queries import QUERY_PROJECT_SNAPSHOT_USER

PAGE_SIZE = 50
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "snapshots"
CAMPOS_CSV = ["sprint", "data_snapshot", "issue_number", "titulo", "status", "assignees", "url"]


def buscar_itens_do_project(token: str, owner: str, number: int) -> list[dict]:
    itens: list[dict] = []
    cursor: str | None = None

    while True:
        data = run_query(
            QUERY_PROJECT_SNAPSHOT_USER,
            {"login": owner, "number": number, "pageSize": PAGE_SIZE, "after": cursor},
            token,
            timeout=30,
        )
        project = data["user"]["projectV2"]
        if project is None:
            raise SystemExit(
                f"Project numero {number} nao encontrado para o usuario '{owner}'. "
                "Confira GITHUB_PROJECT_OWNER/GITHUB_PROJECT_NUMBER no .env "
                "(o numero fica na propria URL do project)."
            )
        pagina = project["items"]
        itens.extend(pagina["nodes"])
        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    return itens


def achatar_item(node: dict, sprint: str, data_snapshot: str) -> dict | None:
    """Transforma um node bruto do GraphQL numa linha de CSV. Ignora draft issues
    (o enunciado exige que todo cartao seja uma Issue de verdade - um draft aqui
    indica algo que ainda precisa virar Issue, entao avisamos em vez de exportar
    como se fosse dado valido)."""
    content = node.get("content") or {}
    status_node = node.get("status")

    if "number" not in content:
        print(f"  [aviso] item sem numero de Issue (draft?) ignorado no snapshot: {content.get('title')!r}")
        return None

    assignees_nodes = content.get("assignees", {}).get("nodes", []) if "assignees" in content else []
    assignees = ";".join(a["login"] for a in assignees_nodes)

    return {
        "sprint": sprint,
        "data_snapshot": data_snapshot,
        "issue_number": content.get("number"),
        "titulo": content.get("title"),
        "status": status_node.get("name") if status_node else None,
        "assignees": assignees,
        "url": content.get("url"),
    }


def salvar_snapshot_csv(linhas: list[dict], sprint: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    caminho = DATA_DIR / f"snapshot_{sprint}.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        writer.writeheader()
        writer.writerows(linhas)
    return caminho


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprint", required=True, help="Identificador da sprint (ex.: S01, S02, S03).")
    args = parser.parse_args()

    token = load_github_token()
    owner, number = load_project_config()
    data_snapshot = date.today().isoformat()

    print(f"Buscando itens do Project #{number} de '{owner}'...")
    nodes = buscar_itens_do_project(token, owner, number)

    linhas = [achatar_item(n, args.sprint, data_snapshot) for n in nodes]
    linhas = [linha for linha in linhas if linha is not None]

    print(f"\n{len(linhas)} item(ns) exportado(s) (de {len(nodes)} no total):\n")
    print(f"{'#':>5}  {'status':15} {'responsavel(is)':20} titulo")
    for linha in linhas:
        print(f"{linha['issue_number']!s:>5}  {str(linha['status']):15} {linha['assignees']:20} {linha['titulo']}")

    caminho_csv = salvar_snapshot_csv(linhas, args.sprint)
    print(f"\nSnapshot salvo em: {caminho_csv}")
    print(
        "\nLembrete: rode este script de novo ao final de CADA sprint (--sprint S01, "
        "S02, S03...) - os snapshots acumulados sao a base de dados dos Labs 04 e 05."
    )


if __name__ == "__main__":
    main()
