## O que observar
Cada barra é a taxa de falsos positivos de um teste quando **não há** correlação (ρ = 0), em 10.000 repetições. A linha tracejada é α = 5%, o valor esperado de um teste bem calibrado; a barra de erro é o IC 95% da taxa. Se o IC inclui a linha, o teste está perto de 5%; se está todo acima, ele é **liberal** (rejeita demais); se está todo abaixo, é **conservador**.

## Conclusão
O **Pearson** é **liberal em todas as situações**: 6,0% nos dados realistas, 6,0% com outliers, 5,8% com assimetria extrema e 7,4% com n = 10. Poucas classes enormes concentram a variância, e a aproximação por t(n − 2) falha. O **Spearman** fica em 5,0% nos dados realistas e 5,2% com outliers, dentro da margem de α, porque trabalha com postos. Ele só se desvia para baixo, ficando **conservador** com assimetria extrema (4,2%) e com n = 10 (3,9%), onde os muitos zeros geram empates e há poucos postos distintos. Em nenhuma situação o Pearson é melhor calibrado que o Spearman.
