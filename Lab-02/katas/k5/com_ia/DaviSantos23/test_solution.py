import pytest
from solution import achatar_dicionario

def test_um_nivel():
    assert achatar_dicionario({"a": 1, "b": 2}) == {"a": 1, "b": 2}

def test_dois_niveis():
    assert achatar_dicionario({"user": {"id": 1, "name": "Bob"}}) == {"user_id": 1, "user_name": "Bob"}

def test_dicionario_vazio():
    assert achatar_dicionario({}) == {}