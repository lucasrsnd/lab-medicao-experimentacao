import re

def extrair_dados_log(log: str) -> dict:
    if not log:
        return {}
        
    padrao = r"^\[(.*?)\]\s+([A-Z]+)\s+(?:([\d\.]+)\s+)?-\s+(.*)$"
    match = re.match(padrao, log)
    
    if not match:
        return {}
        
    timestamp, nivel, ip, mensagem = match.groups()
    
    return {
        "timestamp": timestamp,
        "nivel": nivel,
        "ip": ip if ip else None,
        "mensagem": mensagem
    }