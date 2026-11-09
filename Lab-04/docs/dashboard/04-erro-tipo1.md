## O que observar
Cada barra é a taxa de falsos positivos de um teste quando **não há** correlação (ρ = 0), em 10.000 repetições. A linha tracejada é α = 5%, o valor esperado de um teste bem calibrado; a barra de erro é o IC 95% da taxa. Se o IC inclui a linha, o teste está perto de 5%; se está todo acima, ele é **liberal** (rejeita demais); se está todo abaixo, é **conservador**.

## Conclusão
Com n = 30 e dados realistas, o **Spearman** fica em 5,0%, praticamente em α. Ele continua assim com outliers (5,0%), que limitam sua influência por trabalhar com postos. O **Pearson** já é liberal nos dados realistas (6,0%) e piora com outliers (6,4%) e com n = 10 (6,9%): poucas classes enormes concentram a variância e a aproximação por t(n − 2) falha. O Spearman só se desvia onde há muitos empates ou poucos dados: fica **conservador** com assimetria extrema (4,3%) e com n = 10 (4,1%). Em nenhuma situação o Pearson é melhor calibrado que o Spearman.

*Valores provisórios (exploração com semente 42, 10.000 repetições, repetições sem variação em uma das variáveis contadas como "não rejeita"); atualizar com `outputs/simulacoes.csv` quando o motor Monte Carlo for integrado.*
