"""Snapshot de fechamento de sprint do GitHub Projects -> CSV.

Dono: Lucas, Issue [S01] "Setup do GitHub Projects para o Lab02".

O Lab02 reaproveita o mesmo GitHub Projects (v2) do Lab01, mesma conta
(`GITHUB_PROJECT_OWNER`), mesmo número (`GITHUB_PROJECT_NUMBER`), ver
`.env.example`. Colunas e política de WIP já estavam definidas; o que muda
pro Lab02 é o uso de **Milestones** por sprint (`Lab02S01`, `Lab02S02`,
`Lab02S03`, `Lab02-RelatorioFinal`) para separar as issues por entrega, então
o snapshot aqui também lê e exporta o milestone de cada item (Lab01 não
tinha essa coluna).

Como o GitHub Projects (v2) não guarda histórico de mudança de coluna
consultável via API, este script tira uma "foto" do board no momento em que
roda: cada item (Issue), o status atual (coluna), milestone e responsável(is).
Rodar de novo ao final de cada sprint acumula uma série de snapshots.

Uso (a partir de `Lab-02/`):
    1) preencha no .env: GITHUB_TOKEN, GITHUB_PROJECT_OWNER, GITHUB_PROJECT_NUMBER
    2) python -m src.project.snapshot --sprint Lab02S01

A query usa `user(login: ...)`, não `organization`, porque o Project é de
conta pessoal, mesma base de `Lab-01/src/queries/QUERY_PROJECT_SNAPSHOT_USER`,
com `milestone` a mais.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

from config import GRAPHQL_URL, load_github_token, load_project_config

LAB02_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = LAB02_ROOT / "data" / "snapshots"

PAGE_SIZE = 50
MAX_TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS_S = 3

CAMPOS_CSV = [
    "sprint",
    "data_snapshot",
    "issue_number",
    "titulo",
    "status",
    "milestone",
    "assignees",
    "url",
]

QUERY_PROJECT_SNAPSHOT = """
query SnapshotProject($login: String!, $number: Int!, $pageSize: Int!, $after: String) {
  user(login: $login) {
    projectV2(number: $number) {
      title
      items(first: $pageSize, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          status: fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
          content {
            ... on Issue {
              number
              title
              url
              state
              milestone {
                title
              }
              assignees(first: 5) {
                nodes {
                  login
                }
              }
            }
            ... on PullRequest {
              number
              title
              url
              state
            }
            ... on DraftIssue {
              title
            }
          }
        }
      }
    }
  }
}
"""


@dataclass
class SnapshotRow:
    sprint: str
    data_snapshot: str
    issue_number: int
    titulo: str | None
    status: str | None
    milestone: str | None
    assignees: str
    url: str | None


def run_query(query: str, variables: dict, token: str, timeout: int = 30) -> dict:
    """Executa uma query GraphQL autenticada e devolve o campo `data`.

    Versão enxuta do cliente do Lab-01 (`Lab-01/src/github_client.run_query`):
    o snapshot do Projects lê no máximo umas poucas dezenas de itens, então
    dispensa checkpoint/backoff adaptativo, só um retry simples para falha
    de rede transiente.
    """
    ultimo_erro: Exception | None = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout,
            )
            resposta.raise_for_status()
            corpo = resposta.json()
            if "errors" in corpo:
                sys.exit(f"A API do GitHub retornou erro(s): {corpo['errors']}")
            return corpo["data"]
        except requests.exceptions.RequestException as erro:
            ultimo_erro = erro
            if tentativa < MAX_TENTATIVAS:
                espera = ESPERA_ENTRE_TENTATIVAS_S * (2 ** (tentativa - 1))
                print(f"[aviso] falha de rede (tentativa {tentativa}/{MAX_TENTATIVAS}): {erro}. Tentando de novo em {espera}s...")
                time.sleep(espera)

    sys.exit(f"Falha ao consultar a API do GitHub após {MAX_TENTATIVAS} tentativas: {ultimo_erro}")


def buscar_itens_do_project(token: str, owner: str, number: int) -> list[dict]:
    itens: list[dict] = []
    cursor: str | None = None

    while True:
        data = run_query(
            QUERY_PROJECT_SNAPSHOT,
            {"login": owner, "number": number, "pageSize": PAGE_SIZE, "after": cursor},
            token,
        )
        project = data["user"]["projectV2"]
        if project is None:
            sys.exit(
                f"Project número {number} não encontrado para o usuário '{owner}'. "
                "Confira GITHUB_PROJECT_OWNER/GITHUB_PROJECT_NUMBER no .env "
                "(o número fica na própria URL do project)."
            )
        pagina = project["items"]
        itens.extend(pagina["nodes"])
        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    return itens


def achatar_item(node: dict, sprint: str, data_snapshot: str) -> SnapshotRow | None:
    """Transforma um node bruto do GraphQL numa linha do snapshot.

    Ignora draft issues (o enunciado exige que todo cartão seja uma Issue de
    verdade; um draft aqui indica algo que ainda precisa virar Issue, então
    avisamos em vez de exportar como se fosse dado válido).
    """
    content = node.get("content") or {}
    status_node = node.get("status")

    if "number" not in content:
        print(f"  [aviso] item sem número de Issue (draft?) ignorado no snapshot: {content.get('title')!r}")
        return None

    assignees_nodes = content.get("assignees", {}).get("nodes", []) if "assignees" in content else []
    assignees = ";".join(a["login"] for a in assignees_nodes)
    milestone = content.get("milestone")

    return SnapshotRow(
        sprint=sprint,
        data_snapshot=data_snapshot,
        issue_number=content.get("number"),
        titulo=content.get("title"),
        status=status_node.get("name") if status_node else None,
        milestone=milestone.get("title") if milestone else None,
        assignees=assignees,
        url=content.get("url"),
    )


def salvar_snapshot_csv(linhas: list[SnapshotRow], sprint: str, data_dir: Path = DATA_DIR) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    caminho = data_dir / f"snapshot_{sprint}.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        writer.writeheader()
        for linha in linhas:
            writer.writerow(linha.__dict__)
    return caminho


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--sprint", required=True, help='Identificador da sprint/milestone (ex.: "Lab02S01").'
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    token = load_github_token()
    owner, number = load_project_config()
    data_snapshot = date.today().isoformat()

    print(f"Buscando itens do Project #{number} de '{owner}'...")
    nodes = buscar_itens_do_project(token, owner, number)

    linhas = [achatar_item(n, args.sprint, data_snapshot) for n in nodes]
    linhas = [linha for linha in linhas if linha is not None]

    print(f"\n{len(linhas)} item(ns) exportado(s) (de {len(nodes)} no total):\n")
    print(f"{'#':>5}  {'status':10} {'milestone':15} {'responsavel(is)':20} titulo")
    for linha in linhas:
        print(
            f"{linha.issue_number!s:>5}  {str(linha.status):10} {str(linha.milestone):15} "
            f"{linha.assignees:20} {linha.titulo}"
        )

    caminho_csv = salvar_snapshot_csv(linhas, args.sprint)
    print(f"\nSnapshot salvo em: {caminho_csv}")
    print(
        "\nLembrete: rode este script de novo ao final de CADA sprint (--sprint "
        "Lab02S01, Lab02S02, Lab02S03, Lab02-RelatorioFinal) - os snapshots "
        "acumulados são a base de dados dos Labs 04 e 05."
    )


if __name__ == "__main__":
    main()
