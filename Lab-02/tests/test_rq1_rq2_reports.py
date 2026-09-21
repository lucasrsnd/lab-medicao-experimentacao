"""Smoke test: roda RQ1/RQ2 de ponta a ponta contra os dados reais e confere
que os relatórios saem com a forma esperada (não valida os números em si,
isso é responsabilidade dos testes de stats_utils/dataset com dados
sintéticos)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import rq1_tempo, rq2_defeitos  # noqa: E402


def test_rq1_tempo_main_gera_md_e_json_com_os_dois_cenarios():
    rq1_tempo.main()

    json_path = rq1_tempo.OUT_DIR / "rq1_tempo.json"
    md_path = rq1_tempo.OUT_DIR / "rq1_tempo.md"
    assert json_path.exists()
    assert md_path.exists()

    dados = json.loads(json_path.read_text(encoding="utf-8"))
    assert set(dados.keys()) == {"todos_os_trials", "excluindo_outliers_instrumentacao"}
    for cenario in dados.values():
        assert {"com_ia", "sem_ia"} == {d["tratamento"] for d in cenario["descritivas_por_tratamento"]}
        assert cenario["wilcoxon_pareado_por_integrante"]["n_pares"] == 3

    assert "RQ1" in md_path.read_text(encoding="utf-8")


def test_rq2_defeitos_main_gera_md_e_json_com_as_duas_metricas():
    rq2_defeitos.main()

    json_path = rq2_defeitos.OUT_DIR / "rq2_defeitos.json"
    md_path = rq2_defeitos.OUT_DIR / "rq2_defeitos.md"
    assert json_path.exists()
    assert md_path.exists()

    dados = json.loads(json_path.read_text(encoding="utf-8"))
    for cenario in dados.values():
        assert set(cenario.keys()) == {"taxa_sucesso", "testes_falhando"}

    assert "RQ2" in md_path.read_text(encoding="utf-8")
