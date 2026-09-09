import pytest
from solution import agrupar_anagramas

def test_anagramas_simples():
    resultado = agrupar_anagramas(["abc", "cab", "xyz"])
    # 294 é a soma ASCII de 'a'(97) + 'b'(98) + 'c'(99)
    assert 294 in resultado
    assert set(resultado[294]) == {"abc", "cab"}

def test_lista_vazia():
    assert agrupar_anagramas([]) == {}