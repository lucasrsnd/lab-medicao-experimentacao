# Cenário — Pearson × Spearman: LOC × defeitos (item c)

## Pergunta

O tamanho de um módulo (LOC) está associado ao número de defeitos que ele tem, e qual teste de correlação, Pearson ou Spearman, detecta essa associação de forma mais confiável?

## Hipóteses

- **H0:** não há associação entre LOC e nº de defeitos (ρ = 0).
- **H1:** há associação entre LOC e nº de defeitos (ρ ≠ 0).

**Teste bicaudal (decisão do grupo).** Esperamos associação positiva, mas não vamos descartar a priori a hipótese oposta: um módulo grande com *menos* defeitos também seria um achado, e ignorá-lo seria decidir o resultado antes de olhar os dados. O contrato do projeto também assume p-valor bicaudal nos dois testes, o que mantém a comparação justa (mesmo α = 5% dividido nas duas caudas). Um teste unicaudal só se justificaria com uma razão forte para que o sinal oposto fosse irrelevante, e não é o caso.

O que cada teste verifica: **Pearson** testa a correlação *linear* entre os valores; **Spearman** testa a correlação *monotônica* entre os postos. Ambos usam a estatística t com n − 2 graus de liberdade.

## Dados reais

Apache Ant 1.7, dataset PROMISE (Jureczko & Madeyski), 745 classes Java, das quais 742 com LOC > 0. Amostra de **30 classes** sorteadas com semente 42 (`data/real/amostra.csv`). Detalhes em `data/real/README.md`.

Na amostra: r de Pearson = 0,62 e ρ de Spearman = 0,56; 73% das classes sem defeito; assimetria 2,36 (LOC) e 2,83 (defeitos).

## Como os dados simulados são gerados

Cópula gaussiana: gera-se um par normal com correlação latente ρ e transforma-se cada coordenada na marginal desejada. A correlação latente ρ é o "tamanho do efeito" da simulação: ρ = 0 é H0 verdadeira (variáveis independentes) e ρ > 0 é H1 verdadeira.

| Variável | Distribuição | Parâmetros (estimados da amostra real) |
|---|---|---|
| LOC | Lognormal | μ = 4,92 (mediana ≈ 137 linhas), σ = 1,48 |
| Defeitos | Binomial negativa | média = 0,73, dispersão k = 0,23 (variância = m + m²/k ≈ 3,1) |

**Por que essas escolhas.** LOC e defeitos têm cauda longa à direita nos dados reais, e os defeitos são contagens com muitos zeros e variância bem acima da média, o que a Poisson não captura. A lognormal reproduz a assimetria de LOC e a binomial negativa reproduz zeros e superdispersão. Os parâmetros vêm de `outputs/real_params.json`.

**Tamanhos de efeito:** ρ latente ∈ {0; 0,1; 0,2; 0,3; 0,4; 0,5}, com n = 30 (o mesmo tamanho da amostra real). As situações que violam pressupostos (outliers, amostras pequenas, assimetria extrema) serão definidas na Q3.

## Expectativa registrada antes de simular

> Registrada na Sprint 1, antes de qualquer simulação de Monte Carlo.

**Erro tipo I (Q1).** Esperamos que os dois testes fiquem perto de 5% quando as variáveis são independentes. Sob independência, ambos são válidos; no cenário realista Pearson pode se afastar um pouco, por causa da assimetria e dos muitos zeros com n = 30, enquanto Spearman, que trabalha com postos, deve ficar mais perto de 5%. Com outliers e amostras muito pequenas, esperamos que Pearson seja o que mais se afasta.

**Poder (Q2).** Esperamos que **Spearman tenha mais poder que Pearson no cenário realista**. Pearson mede só a parte linear da associação, e com marginais tão assimétricas alguns poucos módulos enormes dominam o coeficiente, o que atenua a relação e aumenta a variância da estatística. Spearman depende só da ordem dos valores, então não é afetado pela forma das marginais.

**Q3.** Esperamos que a vantagem de Spearman **aumente** com outliers e assimetria extrema. Esperamos que a diferença **encolha ou até inverta** se os dados forem aproximadamente normais, caso em que Pearson tende a ser um pouco mais poderoso.

**Recomendação provisória:** Spearman para este cenário.

## Erros no cenário

- **Erro tipo I:** concluir que LOC está associado a defeitos quando não está. O efeito prático é gastar esforço de revisão ou teste em módulos grandes sem ganho.
- **Erro tipo II:** não detectar uma associação que existe. O efeito prático é deixar passar módulos grandes que concentram defeitos.
- Para priorização de qualidade, o tipo II é mais grave, porque a associação ignorada deixa defeitos sem revisão. Isso favorece o teste com mais poder.
