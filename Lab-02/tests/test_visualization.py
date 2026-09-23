"""Smoke tests para os scripts de gráficos — rodam contra os dados reais e só
conferem que o PNG sai não-vazio. Regressão do bug de 2026-09-23: o dashboard
checava colunas (`tempo`/`sucesso`) que não existem em
`dataset_consolidado.csv` (são `tempo_min`/`testes_passando`+`testes_total`),
e os painéis de RQ1/RQ2 saíam em branco sem erro nenhum — por isso aqui
também confere o tamanho mínimo do arquivo, não só a existência."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.visualization.gerar_dashboard import gerar_dashboard  # noqa: E402
from src.visualization.gerar_grafico_pareado import OUT_DIR, gerar_grafico_pareado  # noqa: E402

# Um painel em branco (só grade 0-1, sem dado) gera um PNG bem menor que um
# painel com boxplot+pontos de verdade — usar um piso de tamanho como proxy
# barato de "o gráfico realmente tem conteúdo", sem precisar decodificar a
# imagem.
TAMANHO_MINIMO_BYTES = 80_000


def test_gerar_dashboard_produz_png_com_conteudo():
    gerar_dashboard()

    caminho = Path("reports/figures/dashboard_tratamentos.png")
    assert caminho.exists()
    assert caminho.stat().st_size > TAMANHO_MINIMO_BYTES


def test_gerar_grafico_pareado_produz_png_com_conteudo():
    gerar_grafico_pareado()

    caminho = OUT_DIR / "rq1_pareado_por_integrante.png"
    assert caminho.exists()
    assert caminho.stat().st_size > 30_000
