# Roteiro da apresentação — Lab04 (P5: Pearson × Spearman)

Até **7 minutos** para as 15 perguntas: cerca de **28 s por resposta**. Cada um responde 5 e conhece todas, porque o professor pode pedir qualquer pergunta a qualquer integrante. Toda resposta aponta para o dashboard: a barra lateral tem as 15 perguntas com link direto para a seção.

| Integrante | Perguntas | Partes que construiu |
|---|---|---|
| **Gustavo** | 1, 6, 13, 14, 15 | dashboard, G2, G4, dados reais e conclusão |
| **Lucas** | 2, 3, 4, 9, 11 | dados reais, cenário, G1, violações e G3 |
| **Davi** | 5, 7, 8, 10, 12 | testes, exemplo simulado, Monte Carlo e poder × n |

## Antes de começar

- [ ] Abrir o link publicado **10 minutos antes**: app sem acesso recente pode hibernar; se aparecer a tela para acordar, clicar e esperar.
- [ ] Plano B no notebook: `cd Lab-04` → `streamlit run streamlit_app.py`.
- [ ] Zoom do navegador em 110–125% para o projetor; barra lateral aberta.
- [ ] Deixar desligada a "nula por permutação" (seção 3); ligar só na pergunta 6.
- [ ] Simulador (seção 5) em: Realista, n = 30, ρ = 0,3.
- [ ] Ensaio cronometrado: as respostas somam ~6,9 min (≈ 1.040 palavras a 150 por minuto). Se estourar, cortar a última frase das respostas 1, 6, 9 e 12, as mais longas.

## Respostas

Os números vêm dos artefatos em `outputs/` (semente 42, 10.000 repetições).

### 1. Qual é o cenário e o que H₀ e H₁ afirmam? — Gustavo
**Mostrar:** topo (cartões "Em resumo") → seção 1.

Queremos saber se classes maiores têm mais defeitos, e qual teste responde isso melhor. Usamos 30 classes Java do Apache Ant 1.7, do dataset PROMISE, com o tamanho em linhas de código e o número de defeitos de cada uma. H₀ diz que não há associação entre tamanho e defeitos, correlação zero. H₁ diz que há associação, positiva ou negativa. Comparamos o Pearson, que olha os valores, com o Spearman, que olha a ordem.

### 2. O teste é unicaudal ou bicaudal? Por quê? — Lucas
**Mostrar:** seção 1 (H₁) e as duas caudas hachuradas do G2.

Bicaudal. Esperamos uma relação positiva, mas não descartamos a negativa antes de ver os dados; escolher uma cauda depois de olhar seria decidir o resultado. Também mantém a comparação justa: os dois testes usam o mesmo α de 5%, dividido em 2,5% em cada cauda. É por isso que o G2 tem região de rejeição dos dois lados, em |t| maior que 2,05.

### 3. Como os dados reais foram coletados e o que mostraram sobre a forma? — Lucas
**Mostrar:** seção 2, G1 (barras cinza).

Usamos o dataset público PROMISE: o Ant 1.7 tem 742 classes com LOC e contagem de defeitos, e sorteamos 30 com semente 42. A forma é muito assimétrica: 73% das classes não têm nenhum defeito, a mediana é de 157 linhas, mas a maior tem 1.842. A assimetria é de 2,4 no LOC e 2,8 nos defeitos, então nenhuma das duas variáveis é parecida com uma normal.

### 4. Como os dados reais ajudaram a escolher os parâmetros? — Lucas
**Mostrar:** seção 2, expander "Parâmetros da simulação" e G1.

Ajustamos uma lognormal ao LOC (mediana de 137 linhas, σ = 1,48) e uma binomial negativa aos defeitos (média 0,73, dispersão 0,23), que reproduz os zeros e a variância bem acima da média. As duas variáveis são ligadas por uma cópula gaussiana com correlação latente ρ: esse ρ é o tamanho do efeito que controlamos. O G1 mostra que o simulado tem a mesma forma do real.

### 5. O que cada teste compara de fato? — Davi
**Mostrar:** seção 3, "Como cada teste funciona".

O Pearson compara os **valores**: mede o quanto LOC e defeitos variam juntos em linha reta, então uma classe enorme pesa muito. O Spearman compara os **postos**, a posição de cada classe na ordem; mede se classes maiores tendem a ter mais defeitos, mesmo sem relação linear, e empates como os zeros recebem o posto médio. Os dois transformam a correlação numa estatística t com n − 2 graus de liberdade.

### 6. No G2: o que é a distribuição sob H₀ e por que a região de rejeição fica onde fica? — Gustavo
**Mostrar:** seção 3, G2; depois ligar "nula por permutação".

A curva preta é a distribuição do t que veríamos se não houvesse associação: t com 28 graus de liberdade. A região de rejeição são as duas caudas, |t| > 2,05, que somam 5% da área: valores tão raros sob H₀ que preferimos rejeitá-la. Ligando a permutação: no Spearman a distribuição real coincide com a curva t; no Pearson ela é irregular, dominada por poucas classes enormes. Isso antecipa o que o G3 confirma.

### 7. O que significa o p-valor do exemplo, e o que ele não significa? — Davi
**Mostrar:** seção 3, área laranja do G2 do Spearman e a tabela.

No exemplo, o Spearman deu t = 2,58 e p = 0,015: se H₀ fosse verdadeira, só 1,5% dos conjuntos de 30 classes dariam um t tão extremo, nas duas caudas. Essa é a área colorida. Ele **não** é a probabilidade de H₀ ser verdadeira, não é a chance de estarmos errando e não mede o tamanho do efeito. Um p pequeno com efeito minúsculo continua sendo efeito minúsculo.

### 8. O que seria erro tipo I e tipo II? Qual é mais grave? — Davi
**Mostrar:** seção 1, "Erros no cenário".

Erro tipo I é concluir que o tamanho está ligado a defeitos quando não está: a equipe gastaria revisão extra em classes grandes sem ganho. Erro tipo II é não detectar uma associação que existe: classes grandes cheias de defeitos ficariam sem atenção. Para priorizar qualidade, o tipo II é mais grave, o que favorece o teste com mais poder, desde que o erro tipo I continue controlado.

### 9. No G3, algum teste se afastou de 5%? Liberal ou conservador, e por quê? — Lucas
**Mostrar:** seção 4, G3 e a tabela de veredictos.

Sim. O Pearson é **liberal em todas as situações**: 6,0% nos dados realistas, 6,0% com outliers, 5,8% com assimetria extrema e 7,4% com n = 10, sempre com o IC inteiro acima de 5%. Poucas classes enormes concentram a variância, e a distribuição t deixa de valer. O Spearman fica em 5,0% e 5,2% nos realistas e com outliers, e só fica conservador, em 4,2% e 3,9%, quando há muitos empates e poucos postos.

### 10. No G4, qual teste tem mais poder? Muda com o efeito? — Davi
**Mostrar:** seção 5, G4 (painel Realista, depois Outliers).

Depende do efeito. Nos dados realistas, o Pearson rejeita um pouco mais até ρ ≈ 0,3, mas parte disso é a mesma liberalidade do G3. A partir daí o Spearman lidera, e a diferença cresce: 57% contra 47% em ρ = 0,5. Com outliers a diferença é enorme: 41% contra 17%. E com n = 30 nenhum dos dois chega a 80% de poder.

### 11. Que violação foi simulada e por que afeta mais um teste? — Lucas
**Mostrar:** seção 4, expander "Como as violações foram simuladas"; G4, painel Outliers.

Simulamos três: outliers em 5% de cada variável, assimetria extrema e amostra pequena com n = 10. Os outliers foram sorteados separadamente em X e Y, para H₀ continuar verdadeira. Eles afetam mais o Pearson porque um ponto extremo domina o produto dos desvios e sozinho cria ou apaga correlação; no Spearman ele vira só "o maior posto". Por isso o poder do Pearson trava em 17%.

### 12. Se usássemos α = 1%, o que mudaria no G3 e no G4? — Davi
**Mostrar:** G3 (linha de 5%) e G4. Os números abaixo foram calculados com o mesmo motor (ver apêndice).

A região de rejeição encolhe para |t| > 2,76, então no G3 todas as taxas caem e a referência vira 1%. O Spearman acompanha, com 0,7% a 1,0%. O Pearson fica **muito mais distorcido**: 3,3% a 4,7%, de três a cinco vezes o nominal, porque erra justamente nas caudas. No G4 todas as curvas descem; por exemplo, o Spearman realista cai de 57% para 31% em ρ = 0,5. Trocamos falso positivo por falso negativo.

### 13. A simulação confirmou o que esperávamos? — Gustavo
**Mostrar:** seção 7, tabela "Esperado × encontrado".

Em boa parte, sim: o Spearman tem mais poder, e o Pearson sofre com outliers e com n pequeno. Houve duas surpresas. Primeiro, o Pearson já é liberal nos dados realistas, com 6%; esperávamos perto de 5%. Segundo, com assimetria extrema a vantagem do Spearman não aumentou: o excesso de zeros gera empates, que tiram poder do Spearman e o deixam conservador.

### 14. Nos dados reais, os testes concordam? O efeito tem importância prática? — Gustavo
**Mostrar:** seção 6, tabela e cartões.

Os dois rejeitam H₀: r = 0,62 e ρ = 0,56, com IC longe de zero. Mas o p do Pearson pela t, 0,0003, é 18 vezes menor que o p por permutação, 0,005; no Spearman os dois conferem, 0,0014 e 0,0011. Na prática, ρ = 0,56 é uma associação grande: revisar primeiro as classes maiores concentra o esforço. Só que o IC é largo e o efeito real pode ser 0,24.

### 15. Qual teste recomendamos, quando mudaríamos e qual a principal limitação? — Gustavo
**Mostrar:** seção 7, "Recomendação", "Quando a escolha mudaria" e "Limitações".

Recomendamos o **Spearman**: controla o erro tipo I em todas as situações, tem mais poder nos dados realistas e com outliers, e seu p-valor confere com a permutação. Mudaríamos para o Pearson com dados aproximadamente normais, por exemplo após log, ou se o interesse fosse uma relação linear para regressão. A principal limitação: uma amostra de 30 classes de um só sistema, então o efeito é incerto e pode não se generalizar.

## Se sobrar tempo ou o professor puxar a seção "Para discutir"

- **Poder com o n real:** com o efeito observado, 30 classes dão 92% de poder ao Spearman e 84% ao Pearson (seção 6, cartões).
- **Quantas observações para 80%:** com o efeito conservador (ρ = 0,24), cerca de 150 classes para o Spearman; o Pearson não chega a 80% nem com 200. Coletar 150 classes é viável num repositório como o Ant; o difícil seria garantir a contagem de defeitos.
- **Resultado não significativo prova que não há efeito?** Não: com poder de ~25% (efeito conservador, n = 30), um "não rejeita" seria o resultado mais provável mesmo com efeito real.
- **Amostras grandes:** com n enorme até ρ = 0,05 fica "significativo"; aí importa o tamanho do efeito e o IC, não o p.
- **O n muda o melhor teste?** Com n = 10 o Pearson rejeita mais, mas com 7,4% de falsos positivos; os pressupostos pesam mais em amostras pequenas. Mostrar no simulador, mudando n.

## Apêndice — números com α = 1% (pergunta 12)

Calculados com o motor oficial (`rejection_rates`), semente 42, 10.000 repetições:

| Situação | Erro tipo I Pearson | Erro tipo I Spearman | Poder ρ = 0,5 Pearson | Poder ρ = 0,5 Spearman |
|---|---|---|---|---|
| Realista | 3,3% | 1,0% | 33% | 31% |
| Outliers | 3,9% | 0,9% | 11% | 20% |
| Assimetria extrema | 4,7% | 0,7% | 26% | 14% |
| Amostra pequena (n = 10) | 4,1% | 0,8% | 20% | 5% |

Para reproduzir, no diretório `Lab-04`:

```powershell
python -c "from lab04.simulation.violations import register_violations; from lab04.simulation.scenarios import all_scenarios; from lab04.simulation.montecarlo import rejection_rates; register_violations(); print(rejection_rates(all_scenarios(), (0.0, 0.3, 0.5), 10_000, 0.01, 42).pivot_table(index=['scenario','effect'], columns='test', values='rate'))"
```
