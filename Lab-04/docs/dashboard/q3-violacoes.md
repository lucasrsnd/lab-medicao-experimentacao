Os três cenários partem dos mesmos parâmetros do cenário realista e mantêm ρ = 0 como hipótese nula: a taxa de rejeição com ρ = 0 mede o erro tipo I, e com ρ > 0 mede o poder sob a violação. Nenhum altera o gerador; usam apenas parâmetros e `Scenario.postprocess`.

## Outliers
**O que muda:** 5% das observações de LOC (classe 10× maior) e 5% das de defeitos (+20 defeitos) são contaminadas. As duas variáveis são sorteadas em separado, com valores que dependem só da própria variável; assim X e Y seguem independentes quando ρ = 0 e H₀ continua verdadeira.
**Por que afeta o Pearson mais:** o Pearson usa os valores, e um ponto extremo domina o produto dos desvios, podendo criar ou apagar uma correlação sozinho. O Spearman usa postos: o mesmo ponto vira apenas "o maior", e sua influência fica limitada.

## Assimetria extrema
**O que muda:** LOC com σ = 2,5 (real: 1,48) e dispersão de defeitos k = 0,05 (real: 0,23), com ainda mais zeros e uma cauda longa de poucas classes enormes.
**Por que afeta o Pearson mais, mas não só ele:** poucos valores gigantes concentram a variância, então o r depende de poucos pontos e sua distribuição se afasta da t(n − 2). O Spearman não sofre disso, mas o excesso de zeros produz empates, e a aproximação t dos postos pode ficar conservadora.

## Amostra pequena (n = 10)
**O que muda:** só o tamanho, de 30 para 10 classes.
**Por que pode afetar os dois:** a distribuição t(n − 2) é uma aproximação, e com 8 graus de liberdade ela é pior para qualquer dos testes. A assimetria dos dados piora o Pearson; o Spearman sofre com a escassez de postos distintos. Com n = 10 também é comum todas as classes terem zero defeito, caso em que a correlação nem existe (nessas repetições o teste não rejeita H₀).
