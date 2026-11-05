## Pergunta e hipóteses
O tamanho de uma classe (LOC) está associado ao número de defeitos? E qual teste de correlação, Pearson ou Spearman, detecta essa associação de forma mais confiável?

- **H₀:** não há associação entre LOC e defeitos (ρ = 0).
- **H₁:** há associação (ρ ≠ 0). Teste **bicaudal**: esperamos uma relação positiva, mas não descartamos a negativa a priori.
- **Dados reais:** 30 classes Java sorteadas com semente 42 entre as 742 com LOC > 0 do Apache Ant 1.7 (dataset PROMISE). Elas calibram a simulação e são analisadas na seção 6.

## Erros no cenário
- **Erro tipo I:** concluir que LOC está associado a defeitos quando não está. Esforço de revisão é gasto em classes grandes sem ganho.
- **Erro tipo II:** não detectar uma associação que existe. Classes grandes que concentram defeitos ficam sem revisão.
- Para priorizar qualidade, o **tipo II é mais grave**, o que favorece o teste com mais poder.
