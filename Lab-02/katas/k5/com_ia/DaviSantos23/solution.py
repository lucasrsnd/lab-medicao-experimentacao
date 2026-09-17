def achatar_dicionario(dicionario, prefixo=""):
    resultado = {}
    
    for chave, valor in dicionario.items():
        nova_chave = f"{prefixo}{chave}"
        
        if isinstance(valor, dict):
            resultado.update(achatar_dicionario(valor, nova_chave + "_"))
    
        else:
            resultado[nova_chave] = valor
            
    return resultado