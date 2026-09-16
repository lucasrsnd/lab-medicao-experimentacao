def achatar_dicionario(d, prefixo=""):
    resultado = {}

    for chave, valor in d.items():
        nova_chave = f"{prefixo}{chave}" if not prefixo else f"{prefixo}_{chave}"

        if isinstance(valor, dict):
            resultado.update(achatar_dicionario(valor, nova_chave))
        else:
            resultado[nova_chave] = valor

    return resultado