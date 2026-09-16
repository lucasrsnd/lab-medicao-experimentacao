def calcular_troco(troco, estoque):
    resultado = {}
    restante = troco

    for nota in sorted(estoque.keys(), reverse=True):
        quantidade = min(restante // nota, estoque[nota])

        if quantidade > 0:
            resultado[nota] = quantidade
            restante -= nota * quantidade

    if restante != 0:
        return None

    return resultado