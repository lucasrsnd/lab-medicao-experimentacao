"""Coleta de métricas estáticas por trial (Radon cc/mi + jscpd + LOC de controle).

Dono: Lucas, Issue [S01] "Script de coleta de métricas estáticas".
Implementação em `static_metrics.py`; CLI: `python -m src.metrics.static_metrics`.

Sem re-export aqui de propósito, ao contrário de outros `__init__.py` que só
têm docstring: este pacote é rodado como script via `-m`, e reexportar o
submódulo no `__init__` faz o Python reimportá-lo como `__main__` e emitir
RuntimeWarning de módulo duplicado. Importe direto de
`src.metrics.static_metrics`.
"""
