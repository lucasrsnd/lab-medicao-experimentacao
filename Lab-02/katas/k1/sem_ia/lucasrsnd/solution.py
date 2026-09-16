def extrair_dados_log(linha):
    if not linha:
        return {}

    try:
        if not linha.startswith("[") or "]" not in linha:
            return {}

        data, restante = linha[1:].split("]", 1)
        partes = restante.strip().split(" - ", 1)

        if len(partes) != 2:
            return {}

        informacoes = partes[0].split()

        if len(informacoes) == 2:
            nivel = informacoes[0]
            ip = informacoes[1]
        elif len(informacoes) == 1:
            nivel = informacoes[0]
            ip = None
        else:
            return {}

        if not data or not nivel or not partes[1]:
            return {}

        return {
            "timestamp": data,
            "nivel": nivel,
            "ip": ip,
            "mensagem": partes[1]
        }

    except (ValueError, IndexError):
        return {}