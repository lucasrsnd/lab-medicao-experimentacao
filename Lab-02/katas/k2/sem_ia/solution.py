def tem_conflito(reunioes):
    ordem = sorted(reunioes)

    for reuniao_atual, proxima_reuniao in zip(ordem, ordem[1:]):
        _, hora_termino = reuniao_atual
        horario_inicio, _ = proxima_reuniao
        if hora_termino > horario_inicio:
            return True

    return False