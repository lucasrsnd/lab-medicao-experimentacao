"""Evita colisão de módulo entre participantes/katas quando o pytest roda mais
de um trial na mesma sessão (ex.: `pytest katas/` a partir da raiz, ou dois
participantes com o mesmo tratamento na mesma pasta de kata). Cada trial usa
os nomes `solution.py`/`test_solution.py`, sem `__init__.py`/namespacing por
pacote — o Python cacheia módulos importados pelo nome curto em
`sys.modules`, e o próprio pytest passa a recusar (import file mismatch) na
2ª vez que vê o mesmo nome de módulo de teste vindo de um arquivo diferente.

Reintroduzido em 2026-09-20: removido por engano em algum commit anterior, o
que já causou pelo menos uma censura falsa (trial K2 Sem IA do Davi, #64) por
"conflito de import do pytest" em vez de dificuldade real da tarefa. Não
remover sem substituir por outra solução equivalente (ex.: __init__.py por
pacote + imports relativos nos test_solution.py).

Não afeta a execução isolada de um trial (`pytest <pasta-do-participante>`,
como o `src/timing/trial_timer.py` já faz) — só importa quando múltiplos
trials são coletados juntos.
"""
import sys

sys.modules.pop("solution", None)
sys.modules.pop("test_solution", None)
