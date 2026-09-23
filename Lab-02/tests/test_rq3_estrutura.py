"""Smoke test: roda RQ3 de ponta a ponta contra os dados reais e confere que
o relatório sai com a forma esperada (mesmo espírito de
`test_rq1_rq2_reports.py` — não valida os números em si)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import rq3_estrutura  # noqa: E402


def test_rq3_estrutura_main_gera_md_e_json_com_todas_as_metricas():
    rq3_estrutura.main()

    json_path = rq3_estrutura.OUT_DIR / "rq3_estrutura.json"
    md_path = rq3_estrutura.OUT_DIR / "rq3_estrutura.md"
    assert json_path.exists()
    assert md_path.exists()

    dados = json.loads(json_path.read_text(encoding="utf-8"))
    assert set(dados.keys()) == {"todos_os_trials", "excluindo_outliers_instrumentacao"}
    for cenario in dados.values():
        assert set(cenario.keys()) == {"complexidade_media", "duplicacao", "sloc", "cc_por_10_sloc", "mi"}
        for metrica in cenario.values():
            assert metrica["wilcoxon_pareado_por_integrante"]["n_pares"] == 3
            assert metrica["wilcoxon_pareado_por_kata"]["n_pares"] == 6

    assert "RQ3" in md_path.read_text(encoding="utf-8")
