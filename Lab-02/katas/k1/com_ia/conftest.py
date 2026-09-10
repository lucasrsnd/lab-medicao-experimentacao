"""Evita colisão do módulo `solution` entre katas quando o pytest roda mais de
um kata na mesma sessão (ex.: `pytest katas/` a partir da raiz). Todos os
katas usam o nome `solution.py`, sem `__init__.py`/namespacing por pacote, e
o Python cacheia módulos importados pelo nome curto em `sys.modules` — sem
isso, o 2º kata importado no mesmo processo reaproveitaria o `solution.py`
do 1º em vez do seu próprio.

Não afeta a execução isolada de um trial (`pytest <pasta-do-kata>`, como o
`src/timing/trial_timer.py` já faz) — só importa quando múltiplos katas são
coletados juntos.
"""
import sys

sys.modules.pop("solution", None)
