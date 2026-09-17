import pytest
from solution import extrair_dados_log

def test_linha_log_valida():
    log = "[2026-03-10 10:15:30] ERROR 192.168.1.10 - Falha na conexao"
    esperado = {
        "timestamp": "2026-03-10 10:15:30",
        "nivel": "ERROR",
        "ip": "192.168.1.10",
        "mensagem": "Falha na conexao"
    }
    assert extrair_dados_log(log) == esperado

def test_linha_log_sem_ip():
    log = "[2026-03-10 10:16:00] INFO - Servidor reiniciado"
    esperado = {
        "timestamp": "2026-03-10 10:16:00",
        "nivel": "INFO",
        "ip": None,
        "mensagem": "Servidor reiniciado"
    }
    assert extrair_dados_log(log) == esperado

def test_linha_log_vazia():
    assert extrair_dados_log("") == {}