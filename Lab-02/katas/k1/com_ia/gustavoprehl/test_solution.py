import pytest
from solution import parse_log

def test_parse_linha_completa_com_ip():
    linha = "[2023-11-20 15:30:45] ERROR 192.168.0.15 - Timeout na base de dados"
    resultado = parse_log(linha)
    assert resultado == {
        "timestamp": "2023-11-20 15:30:45",
        "nivel": "ERROR",
        "ip": "192.168.0.15",
        "mensagem": "Timeout na base de dados"
    }

def test_parse_linha_sem_ip():
    linha = "[2023-11-20 15:30:46] INFO - Reconexão estabelecida"
    resultado = parse_log(linha)

    assert resultado == {
        "timestamp": "2023-11-20 15:30:46",
        "nivel": "INFO",
        "ip": None,
        "mensagem": "Reconexão estabelecida"
    }

def test_retorna_dicionario_vazio_string_vazia():
    assert parse_log("") == {}
    assert parse_log("    ") == {}
    assert parse_log(None) == {}

def test_retorna_dicionario_vazio_mal_formatado():
    assert parse_log("2023-11-20 15:30:45 INFO - Mensagem") == {}

    assert parse_log("[2023-11-20 15:30:45] INFO Mensagem") == {}

    assert parse_log("Isso não é um log") == {}

def test_parse_linha_com_espacos_extras():
    linha = "   [2023-11-20 15:30:45] WARNING 10.0.0.5 - Espaço em disco baixo   "
    resultado = parse_log(linha)

    assert resultado["timestamp"] == "2023-11-20 15:30:45"
    assert resultado["nivel"] == "WARNING"
    assert resultado["ip"] == "10.0.0.5"
    assert resultado["mensagem"] == "Espaço em disco baixo"
