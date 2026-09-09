import pytest
from solution import calcular_troco

def test_troco_exato_disponivel():
    assert calcular_troco(70, {50: 1, 20: 2, 10: 5}) == {50: 1, 20: 1}

def test_troco_com_notas_menores():
    assert calcular_troco(40, {50: 1, 20: 1, 10: 5}) == {20: 1, 10: 2}

def test_troco_impossivel():
    assert calcular_troco(30, {50: 1, 20: 1}) == None