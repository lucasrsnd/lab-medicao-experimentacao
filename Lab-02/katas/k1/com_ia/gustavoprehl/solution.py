import re

def parse_log(linha: str) -> dict:
    if not linha or not isinstance(linha, str) or not linha.strip():
        return {}

    padrao = (
        r'^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] '
        r'(?P<nivel>[A-Z]+) '
        r'(?:(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) )?'
        r'- (?P<mensagem>.+)$'
    )

    match = re.match(padrao, linha.strip())
    if not match:
        return {}

    return {
        "timestamp": match.group("timestamp"),
        "nivel": match.group("nivel"),
        "ip": match.group("ip"),
        "mensagem": match.group("mensagem"),
    }
