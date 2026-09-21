"""Reset por participante do cache de módulo (ver conftest.py do tratamento,
um nível acima, para a explicação completa). Necessário aqui também porque
quando dois participantes compartilham o mesmo kata+tratamento, o pop() do
conftest.py do tratamento só roda uma vez (na 1ª pasta visitada) — sem este
aqui, o 2º participante colidiria com o 1º.
"""
import sys

sys.modules.pop("solution", None)
sys.modules.pop("test_solution", None)
