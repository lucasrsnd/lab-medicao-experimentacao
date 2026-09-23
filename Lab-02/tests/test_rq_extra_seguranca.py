"""Smoke test da análise extra de segurança — roda contra os dados reais."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import rq_extra_seguranca  # noqa: E402


def test_rq_extra_seguranca_main_gera_md_e_json():
    rq_extra_seguranca.main()

    json_path = rq_extra_seguranca.OUT_DIR / "rq_extra_seguranca.json"
    md_path = rq_extra_seguranca.OUT_DIR / "rq_extra_seguranca.md"
    assert json_path.exists()
    assert md_path.exists()

    dados = json.loads(json_path.read_text(encoding="utf-8"))
    assert dados["n_trials"] == 18
    assert {"com_ia", "sem_ia"} == {d["tratamento"] for d in dados["descritivas_por_tratamento"]}
    assert dados["wilcoxon_pareado_por_integrante"]["n_pares"] == 3

    assert "Vulnerabilidades" in md_path.read_text(encoding="utf-8")
