def agrupar_anagramas(palavras):
    grupo_letras = {}

    for palavra in palavras:
        letras_ordenadas = tuple(sorted(palavra))
        grupo_letras.setdefault(letras_ordenadas, []).append(palavra)

    resultado = {}
    for letras_ordenadas, grupo in grupo_letras.items():

        soma = sum(ord(letra) for letra in letras_ordenadas)
        resultado[soma] = grupo

    return resultado