def is_valid_password(password: str) -> bool:
    """
    Valida se uma senha é forte de acordo com os critérios:
    - 8 caracteres;
    - Ao mínimo 2 caracteres maiúsculos;
    - Caracteres maiúsculos não podem estar juntos;
    - Nenhum caractere se repete 3x ou mais em sequência
    """
    if len(password) < 8:
        return False

    upper_count = 0

    for i in range(len(password)):
        current_char = password[i]

        if current_char.isupper():
            upper_count += 1
            if i < len(password) - 1 and password[i+1].isupper():
                return False

        if i < len(password) - 2:
            if current_char == password[i+1] == password[i+2]:
                return False

    if upper_count < 2:
        return False

    return True
