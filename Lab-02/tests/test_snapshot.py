"""Testes de src/project/snapshot.py com `run_query` mockado - zero chamadas
reais à API. Mesma técnica de `Lab-01/tests/test_pagination.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.project.snapshot import (  # noqa: E402
    achatar_item,
    buscar_itens_do_project,
    salvar_snapshot_csv,
)


def _item_issue(number: int, status: str | None, milestone: str | None, assignees: list[str]) -> dict:
    return {
        "status": {"name": status} if status else None,
        "content": {
            "number": number,
            "title": f"Issue {number}",
            "url": f"https://github.com/x/y/issues/{number}",
            "state": "OPEN",
            "milestone": {"title": milestone} if milestone else None,
            "assignees": {"nodes": [{"login": a} for a in assignees]},
        },
    }


def _item_draft(title: str) -> dict:
    return {"status": {"name": "Backlog"}, "content": {"title": title}}


def _pagina(nodes: list[dict], has_next: bool, cursor: str | None) -> dict:
    return {"user": {"projectV2": {"title": "Lab", "items": {"pageInfo": {"hasNextPage": has_next, "endCursor": cursor}, "nodes": nodes}}}}


def test_achatar_item_issue_completa() -> None:
    node = _item_issue(12, "Doing", "Lab02S01", ["lucasrsnd", "gustavoprehl"])

    linha = achatar_item(node, sprint="Lab02S01", data_snapshot="2026-09-09")

    assert linha is not None
    assert linha.issue_number == 12
    assert linha.status == "Doing"
    assert linha.milestone == "Lab02S01"
    assert linha.assignees == "lucasrsnd;gustavoprehl"
    assert linha.sprint == "Lab02S01"


def test_achatar_item_sem_status_ou_milestone() -> None:
    node = _item_issue(13, None, None, [])

    linha = achatar_item(node, sprint="Lab02S01", data_snapshot="2026-09-09")

    assert linha is not None
    assert linha.status is None
    assert linha.milestone is None
    assert linha.assignees == ""


def test_achatar_item_ignora_draft_issue() -> None:
    node = _item_draft("Rascunho sem virar Issue")

    linha = achatar_item(node, sprint="Lab02S01", data_snapshot="2026-09-09")

    assert linha is None


def test_buscar_itens_do_project_pagina_ate_o_fim() -> None:
    respostas = [
        _pagina([_item_issue(1, "Backlog", "Lab02S01", [])], True, "cursor1"),
        _pagina([_item_issue(2, "Doing", "Lab02S01", [])], False, None),
    ]

    with patch("src.project.snapshot.run_query", side_effect=respostas) as mock_run:
        itens = buscar_itens_do_project("token", "lucasrsnd", 2)

    assert len(itens) == 2
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0].args[1]["after"] is None
    assert mock_run.call_args_list[1].args[1]["after"] == "cursor1"


def test_buscar_itens_do_project_encerra_se_project_nao_existe() -> None:
    resposta = {"user": {"projectV2": None}}

    with patch("src.project.snapshot.run_query", return_value=resposta):
        try:
            buscar_itens_do_project("token", "lucasrsnd", 999)
            assert False, "deveria ter chamado sys.exit"
        except SystemExit:
            pass


def test_salvar_snapshot_csv_grava_cabecalho_e_linhas(tmp_path: Path) -> None:
    linhas = [achatar_item(_item_issue(1, "Done", "Lab02S01", ["lucasrsnd"]), "Lab02S01", "2026-09-09")]

    caminho = salvar_snapshot_csv(linhas, "Lab02S01", data_dir=tmp_path)

    conteudo = caminho.read_text(encoding="utf-8").strip().splitlines()
    assert conteudo[0] == "sprint,data_snapshot,issue_number,titulo,status,milestone,assignees,url"
    assert "Lab02S01,2026-09-09,1,Issue 1,Done,Lab02S01,lucasrsnd" in conteudo[1]
