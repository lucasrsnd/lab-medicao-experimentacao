def agrupar_anagramas(palavras):
    grupos = {}  # chave: (soma_ascii, letras_ordenadas) -> lista de palavras

    for palavra in palavras:
        soma_ascii = sum(ord(c) for c in palavra)
        letras_ordenadas = "".join(sorted(palavra))
        chave_interna = (soma_ascii, letras_ordenadas)
        grupos.setdefault(chave_interna, []).append(palavra)

    resultado = {}
    for (soma_ascii, _), lista in grupos.items():
        resultado[soma_ascii] = lista

    return resultado