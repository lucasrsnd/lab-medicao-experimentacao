def calcular_troco(valor_troco, estoque):
    resultado = {}
    
    notas = sorted(estoque.keys(), reverse=True)
    
    for nota in notas:
        quantidade_disponivel = estoque[nota]
        
        if quantidade_disponivel > 0 and valor_troco >= nota:
            quantidade_necessaria = valor_troco // nota
            
            quantidade_usada = min(quantidade_necessaria, quantidade_disponivel)
            
            if quantidade_usada > 0:
                resultado[nota] = quantidade_usada
                valor_troco -= nota * quantidade_usada
                
    if valor_troco == 0:
        return resultado
        
    return None