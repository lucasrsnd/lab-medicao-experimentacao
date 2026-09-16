import pytest
from solution import tem_conflito

def test_sem_conflito():
    assert tem_conflito([(10, 12), (12, 14), (15, 16)]) == False

def test_com_conflito():
    assert tem_conflito([(10, 12), (11, 13)]) == True

def test_lista_vazia():
    assert tem_conflito([]) == False