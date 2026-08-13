"""Testes de `src.github_client.paginate_resumable()` com `run_query` mockado -
zero chamadas reais à API. Rodar com: `python -m unittest` (a partir de Lab-01/,
com `pip install -e .` já feito).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.github_client import GraphQLTransientError, paginate_resumable


def _pagina(nodes: list[dict], has_next: bool, cursor: str, rate_limit_restante: int = 5000) -> dict:
    """Monta uma resposta `data` no formato que `run_query` devolveria."""
    return {
        "rateLimit": {"remaining": rate_limit_restante, "resetAt": "2099-01-01T00:00:00Z"},
        "search": {
            "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
            "nodes": nodes,
        },
    }


class TestPaginateResumable(unittest.TestCase):
    def setUp(self):
        self._tmpdir = TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.checkpoint_path = Path(self._tmpdir.name) / ".checkpoint_teste.json"
        # evita que os testes esperem de verdade os sleeps entre paginas/retries
        self._sleep_patcher = patch("src.github_client.time.sleep")
        self.mock_sleep = self._sleep_patcher.start()
        self.addCleanup(self._sleep_patcher.stop)

    def test_caminho_feliz_varias_paginas(self):
        respostas = [
            _pagina([{"id": 1}, {"id": 2}], True, "cursor1"),
            _pagina([{"id": 3}, {"id": 4}], True, "cursor2"),
            _pagina([{"id": 5}], False, "cursor3"),
        ]
        with patch("src.github_client.run_query", side_effect=respostas) as mock_run:
            repos = paginate_resumable(
                "QUERY", {}, "token",
                total=5, checkpoint_path=self.checkpoint_path, page_size_inicial=2,
            )

        self.assertEqual([r["id"] for r in repos], [1, 2, 3, 4, 5])
        self.assertEqual(mock_run.call_count, 3)
        # primeira pagina sem cursor, demais usando o endCursor devolvido antes
        self.assertIsNone(mock_run.call_args_list[0].args[1]["after"])
        self.assertEqual(mock_run.call_args_list[1].args[1]["after"], "cursor1")
        self.assertEqual(mock_run.call_args_list[2].args[1]["after"], "cursor2")
        # checkpoint eh removido ao concluir com sucesso
        self.assertFalse(self.checkpoint_path.exists())

    def test_page_size_reduz_pela_metade_apos_falha(self):
        respostas = [
            GraphQLTransientError("502"),
            _pagina([{"id": 1}], False, "cursor1"),  # hasNextPage=False encerra o loop aqui
        ]
        with patch("src.github_client.run_query", side_effect=respostas) as mock_run:
            paginate_resumable(
                # total bem maior que os nodes devolvidos, de proposito: garante que o
                # `min(page_size, restantes)` do laco nao mascare o page_size real enviado
                "QUERY", {}, "token",
                total=100, checkpoint_path=self.checkpoint_path,
                page_size_inicial=30, page_size_min=5,
            )

        # 1a tentativa com page_size inicial (30), 2a ja reduzida pela metade (15)
        self.assertEqual(mock_run.call_args_list[0].args[1]["pageSize"], 30)
        self.assertEqual(mock_run.call_args_list[1].args[1]["pageSize"], 15)

    def test_retoma_do_checkpoint_existente(self):
        checkpoint = {
            "total": 3,
            "cursor": "cursor_salvo",
            "page_size": 10,
            "repos": [{"id": 1}, {"id": 2}],
        }
        self.checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

        with patch("src.github_client.run_query", return_value=_pagina([{"id": 3}], False, "cursor_final")) as mock_run:
            repos = paginate_resumable(
                "QUERY", {}, "token", total=3, checkpoint_path=self.checkpoint_path,
            )

        self.assertEqual([r["id"] for r in repos], [1, 2, 3])
        # so precisou de 1 chamada (ja tinha 2 de 3 no checkpoint) e partiu do cursor salvo
        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(mock_run.call_args.args[1]["after"], "cursor_salvo")

    def test_ignora_checkpoint_de_total_diferente(self):
        checkpoint = {"total": 999, "cursor": "x", "page_size": 10, "repos": [{"id": 99}]}
        self.checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

        with patch("src.github_client.run_query", return_value=_pagina([{"id": 1}], False, "c1")):
            repos = paginate_resumable(
                "QUERY", {}, "token", total=1, checkpoint_path=self.checkpoint_path,
            )

        # nao deve conter o repo "fantasma" do checkpoint de outro total
        self.assertEqual([r["id"] for r in repos], [1])

    def test_pausa_quando_rate_limit_baixo(self):
        respostas = [
            _pagina([{"id": 1}], False, "cursor1", rate_limit_restante=10),
        ]
        with patch("src.github_client.run_query", side_effect=respostas):
            paginate_resumable(
                "QUERY", {}, "token", total=1, checkpoint_path=self.checkpoint_path,
            )

        self.assertTrue(self.mock_sleep.called)

    def test_desiste_e_salva_checkpoint_apos_falhas_seguidas(self):
        with patch("src.github_client.run_query", side_effect=GraphQLTransientError("502 persistente")):
            with self.assertRaises(SystemExit):
                paginate_resumable(
                    "QUERY", {}, "token", total=100, checkpoint_path=self.checkpoint_path,
                    max_falhas_seguidas=3, page_size_inicial=10, page_size_min=5,
                )

        self.assertTrue(self.checkpoint_path.exists())
        salvo = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        self.assertEqual(salvo["repos"], [])  # nenhuma pagina completou

    def test_total_acima_do_limite_da_search_api_e_rejeitado(self):
        with self.assertRaises(ValueError):
            paginate_resumable(
                "QUERY", {}, "token", total=1001, checkpoint_path=self.checkpoint_path,
            )


if __name__ == "__main__":
    unittest.main()
