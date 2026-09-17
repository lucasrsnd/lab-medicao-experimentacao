import pytest
from solution import validar_senha

def test_senha_valida():
    assert validar_senha("AbcdefGh") == True

def test_senha_curta():
    assert validar_senha("AbcD") == False

def test_maiusculas_adjacentes():
    assert validar_senha("ABcdefgh") == False

def test_repeticao_tripla():
    assert validar_senha("AbcdefffG") == False