## O que observar
Em cada faixa, compare a barra cinza (30 classes reais) com a verde ao lado (10.000 classes simuladas): as duas distribuições devem ter a mesma forma.

## Conclusão
LOC e defeitos têm cauda longa à direita (assimetrias de 2,4 e 2,8) e 73% das classes não têm defeito. Por isso simulamos LOC com uma **lognormal** (mediana ≈ 137 linhas, σ = 1,48) e defeitos com uma **binomial negativa** (média 0,73, dispersão 0,23), que reproduzem a assimetria, os zeros e a variância muito acima da média. A amostra real, com só 30 classes, é mais irregular, mas o formato geral coincide.
