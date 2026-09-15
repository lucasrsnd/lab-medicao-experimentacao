from collections import defaultdict

def group_anagrams_by_weight(words: list [str]) -> dict:
    """
    Agrupa uma lista de palavras verificando se são anagramas.

    A chave do dicionário de retorno é uma tupla contendo a soma dos valores
    ASCII das letras e a string ordenada. Isso garante que falsos positivos
    (palavras não anagramas com mesma soma ASCII) fiquem em chaves distintas.
    """
    if not words:
        return {}

    groups = defaultdict(list)
    for word in words:
        ascii_sum = sum(ord(char)for char in word)
        sorted_word = "".join(sorted(word))
        key = (ascii_sum, sorted_word)
        groups[key].append(word)
    return dict(groups)
