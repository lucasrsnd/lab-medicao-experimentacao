def validar_senha(senha):
    if len(senha) < 8:
        return False

    maiusculas = [i for i, letra in enumerate(senha) if letra.isupper()]
    if len(maiusculas) < 2:
        return False

    for i, j in zip(maiusculas, maiusculas[1:]):
        if j - i == 1:
            return False

    for i in range(len(senha) - 2):
        if senha[i] == senha[i + 1] == senha[i + 2]:
            return False

    return True