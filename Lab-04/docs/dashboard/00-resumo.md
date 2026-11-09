## Pergunta
O tamanho de uma classe (LOC) está associado ao número de defeitos? E qual teste, **Pearson** ou **Spearman**, responde isso com mais confiança?

## Expectativa
Spearman deve ter **mais poder** e manter o erro tipo I perto de 5%; Pearson deve sofrer com a assimetria dos dados e com outliers.

## Resultado
**Usar o Spearman.** O Pearson é liberal em todas as situações (5,8% a 7,4% de falsos positivos); o Spearman fica em 5% ou abaixo e lidera em poder a partir de ρ ≈ 0,3. Nos dados reais, os dois detectam a associação (ρ = 0,56), mas só o p-valor do Spearman confere com a permutação.
