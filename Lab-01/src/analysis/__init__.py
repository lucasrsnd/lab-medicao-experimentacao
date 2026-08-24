"""Estatísticas e gráficos para o relatório final (Lab01S03).

`stats.py`: funções puras (DataFrame -> números/dicts) - uma por RQ.
`figures.py`: gera as figuras (matplotlib) a partir de `stats.py`, salva em
`Lab-01/reports/figures/`.

Reaproveitado tanto por `scripts/gerar_relatorio_figuras.py` (figuras estáticas pro
relatório) quanto por `app_streamlit.py` (dashboard interativo) - mesma fonte de
verdade nos dois lugares, sem duplicar cálculo.

Cobertura atual: RQ01, RQ02 (Issue #15). RQ03-04 (#16) e RQ05-07 (#17) entram
conforme essas Issues avançam.
"""
