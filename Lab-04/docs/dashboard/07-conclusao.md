## Esperado × encontrado
| | Esperávamos (registrado antes de simular) | Encontramos |
|---|---|---|
| Erro tipo I | Os dois perto de 5%; o Pearson podendo se afastar um pouco | O **Pearson é liberal em todas as situações** (5,8% a 7,4%); o Spearman fica em 5% ou abaixo (3,9% a 5,2%) |
| Poder nos dados realistas | Spearman mais poderoso | **Confirmado** a partir de ρ ≈ 0,3 (57% × 47% em ρ = 0,5); abaixo disso o Pearson rejeita mais, mas inflado pela liberalidade |
| Outliers | Vantagem do Spearman aumenta | **Confirmado**: 41% × 17% em ρ = 0,5 |
| Assimetria extrema | Vantagem do Spearman aumenta | **Não confirmado**: o Pearson fica à frente até ρ = 0,4; os empates (excesso de zeros) tiram poder do Spearman |
| Amostra pequena (n = 10) | Pearson se afasta mais de 5% | **Confirmado**: 7,4% de falsos positivos, contra 3,9% do Spearman |
| Dados reais | — | Os dois rejeitam H₀, mas o p-valor t do Pearson é cerca de 18× mais otimista que o da permutação |

## Recomendação
Para testar a associação entre LOC e defeitos, usar o **Spearman**. Ele mantém o erro tipo I sob controle em todas as situações, tem mais poder nos dados realistas e com outliers, e nos dados reais seu p-valor coincide com o da permutação. Reportar o ρ com IC 95%, não só o p-valor.

## Quando a escolha mudaria
- **Dados aproximadamente normais**, sem cauda longa nem outliers (por exemplo, métricas já transformadas em log): aí o Pearson é o teste mais poderoso para associação linear. Esse cenário não foi simulado.
- **Interesse explícito em relação linear**, como prever defeitos a partir de LOC com regressão.
- Se for preciso usar o Pearson nestes dados, calcular o **p-valor por permutação**, não pela aproximação t.

## Limitações
- **Uma única amostra real** de 30 classes de um só sistema (Apache Ant 1.7): o efeito é incerto (IC do ρ de 0,24 a 0,76) e pode não valer para outros projetos.
- A simulação usa **cópula gaussiana** com marginais lognormal e binomial negativa; outras formas de dependência não foram testadas.
- O efeito simulado é a correlação **latente**; a conversão do ρ observado é uma calibração pela média e ignora a variação amostral.
