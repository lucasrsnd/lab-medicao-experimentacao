def validar_senha(senha):
    if len(senha) < 8:
        return False

    for i in range(len(senha) - 2):
        if senha[i] == senha[i + 1] == senha[i + 2]:
            return False

    total_maiusculas = 0
    for i, char in enumerate(senha):
        if char.isupper():
            total_maiusculas += 1
            if i > 0 and senha[i - 1].isupper():
                return False

    if total_maiusculas < 2:
        return False

    return True

