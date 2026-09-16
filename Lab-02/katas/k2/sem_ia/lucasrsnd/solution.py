def tem_conflito(reunioes):
    reunioes = sorted(reunioes)

    for i in range(len(reunioes) - 1):
        if reunioes[i][1] > reunioes[i + 1][0]:
            return True

    return False